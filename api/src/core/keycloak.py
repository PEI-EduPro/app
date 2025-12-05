# src/core/keycloak.py
import asyncio
from keycloak import KeycloakOpenID, KeycloakAdmin # Import KeycloakAdmin
from src.core.settings import settings
import logging

logger = logging.getLogger(__name__)

class KeycloakClient:
    def __init__(self):
        self.client = KeycloakOpenID(
            server_url=settings.KEYCLOAK_SERVER_URL,
            client_id=settings.KEYCLOAK_CLIENT_ID, # 'api-backend'
            realm_name=settings.KEYCLOAK_REALM,    # 'master'
            client_secret_key=settings.KEYCLOAK_CLIENT_SECRET, # Secret for 'api-backend'
        )
        
        # Initialize the Keycloak Admin client using the 'api-backend' client credentials
        # This assumes 'api-backend' client is configured as 'confidential' in the 'master' realm
        # and has admin roles assigned to its service account via 'realm-management'.
        try:
            self.admin_client = KeycloakAdmin(
                server_url=settings.KEYCLOAK_SERVER_URL,
                username=None, # Do not use username/password for service accounts
                password=None, # Do not use username/password for service accounts
                realm_name=settings.KEYCLOAK_REALM, # 'master'
                client_id=settings.KEYCLOAK_CLIENT_ID, # 'api-backend'
                client_secret_key=settings.KEYCLOAK_CLIENT_SECRET, # Secret for 'api-backend'
                verify=True # Set to False if using self-signed certificates in dev
            )
            
            logger.info("Keycloak Admin client (via Service Account) initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Keycloak Admin client: {e}")
            # Depending on your needs, you might want to prevent startup or handle gracefully
            self.admin_client = None
            self.admin_init_error = e

        # Pre-fetch the public key for token verification (optional, might be done by OpenID client)
        try:
            public_key = self.client.public_key()
            logger.info("Keycloak client public key fetched successfully.")
        except Exception as e:
            logger.error(f"Failed to fetch Keycloak client public key: {e}")

    async def verify_token(self, token: str) -> dict | None:
        """Verify JWT token using the Keycloak client's built-in method."""
        logger.debug(f"Starting verification for token: {token[:50]}...")

        try:
            loop = asyncio.get_event_loop()
            # Use the simplest form of decode_token that works with your library version
            token_info = await loop.run_in_executor(
                None,
                lambda: self.client.decode_token(token)
            )
            
            # Manual issuer verification
            expected_issuer = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}"
            actual_issuer = token_info.get('iss', '')
            
            if actual_issuer != expected_issuer:
                logger.error(f"Issuer mismatch. Expected: {expected_issuer}, Got: {actual_issuer}")
                return None
            
            # Manual audience check - allow both 'account' and the client ID
            allowed_audiences = ['account', settings.KEYCLOAK_CLIENT_ID]
            token_audience = token_info.get('aud', [])
            
            # Handle both string and list audience formats
            if isinstance(token_audience, str):
                token_audience = [token_audience]
            
            if not any(aud in allowed_audiences for aud in token_audience):
                logger.error(f"Audience mismatch. Expected one of {allowed_audiences}, Got: {token_audience}")
                return None
            
            logger.info(f"Token verified successfully for user: {token_info.get('preferred_username', token_info.get('sub', 'unknown'))}")
            logger.debug(f"Full token info: {token_info}")
            return token_info

        except Exception as e:
            # Catch all errors during verification
            logger.error(f"Token verification failed with error: {e}")
            logger.exception(e)  # Log the full traceback
            return None

    async def create_user_in_keycloak(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str = None,
        last_name: str = None,
        temporary: bool = False,
        realm_role: str = None,
        nmec: str = None
    ) -> dict:
        """
        Create a new user in Keycloak using the Admin API via Service Account.
        Optionally assign a realm role.
        """
        # Check if admin client was initialized successfully
        if not self.admin_client:
            logger.error(f"Cannot create user: Admin client not initialized. Error during init: {getattr(self, 'admin_init_error', 'Unknown error')}")
            raise RuntimeError("Keycloak Admin client not available. Check server logs and configuration.")

        logger.info(f"Attempting to create user: {username} in realm: {settings.KEYCLOAK_REALM}")
        try:
            loop = asyncio.get_event_loop()
            
            # Prepare the user data dictionary
            user_data = {
                "username": username,
                "email": email,
                "enabled": True, # Enable user by default
                "emailVerified": True, # Assume email is verified during creation
                "credentials": [
                    {
                        "type": "password",
                        "value": password,
                        "temporary": temporary # Set temporary flag
                    }
                ],
                # Initialize attributes dictionary, even if empty
                "attributes": {}
            }

            # Add optional standard fields if they are provided
            if first_name:
                user_data["firstName"] = first_name
            if last_name:
                user_data["lastName"] = last_name
            # Add the nmec as an attribute if provided
            if nmec is not None: # Check explicitly for None, not just falsy
                user_data["attributes"]["nmec"] = nmec # Add nmec to the existing attributes dict

            # Call the Keycloak Admin API to create the user
            user_id = await loop.run_in_executor(
                None,
                lambda: self.admin_client.create_user(user_data) # Pass the correctly structured user_data
            )
            logger.info(f"User {username} created successfully with ID: {user_id}")

            # Assign realm role if specified
            if realm_role:
                logger.info(f"Attempting to assign role '{realm_role}' to user {username} (ID: {user_id})")
                # Get the role ID first
                role_id = await loop.run_in_executor(
                    None,
                    lambda: self.admin_client.get_realm_role(realm_role)['id']
                )
                # Assign the role
                await loop.run_in_executor(
                    None,
                    lambda: self.admin_client.assign_realm_roles(
                        user_id=user_id,
                        roles=[{"id": role_id, "name": realm_role}]
                    )
                )
                logger.info(f"Role '{realm_role}' assigned to user {username} successfully.")

            return {"user_id": user_id, "message": "User created successfully"}

        except Exception as e:
            # Catch all errors during creation
            # Common errors might be KeycloakGetError, KeycloakPostError, etc. depending on the library version
            error_msg = str(e)
            logger.error(f"Keycloak Admin API error during user creation: {error_msg}")
            logger.exception(e) # Log the full traceback

            # Handle specific errors like user already exists, role not found, etc.
            # These error messages can vary depending on the Keycloak server version and python-keycloak version
            if "User exists with same username" in error_msg or "User exists with same email" in error_msg:
                 raise ValueError(f"User with username '{username}' or email '{email}' already exists.")
            if "Role not found" in error_msg or "Role with name" in error_msg and "does not exist" in error_msg:
                 raise ValueError(f"Realm role '{realm_role}' not found.")
            # Raise a generic error for other issues
            raise e # Re-raise to be handled by the endpoint


    def get_user_roles(self, token_info: dict) -> list[str]:
        """Extract user roles from token"""
        realm_access = token_info.get("realm_access", {})
        return realm_access.get("roles", [])

    def get_user_groups(self, token_info: dict) -> list[str]:
        """Extract user groups from token"""
        return token_info.get("groups", [])

    def has_role(self, token_info: dict, role: str) -> bool:
        """Check if user has specific role"""
        roles = self.get_user_roles(token_info)
        return role in roles

    def has_group(self, token_info: dict, group: str) -> bool:
        """Check if user is in specific group"""
        groups = self.get_user_groups(token_info)
        return group in groups
    
    async def create_subject_groups_and_assign_regent(
        self,
        subject_id: str, # Use the database subject ID as part of the group name
        regent_keycloak_id: str
    ) -> bool:
        """
        Creates the base subject group and all its subgroups in Keycloak using a flat structure.
        Assigns the specified user as the regent by adding them to the /s{subject_id}/regent group.
        """
        logger.info(f"Creating groups for subject ID: {subject_id}, assigning regent: {regent_keycloak_id}")

        try:
            loop = asyncio.get_event_loop()

            # Define the group hierarchy using flat names with a prefix
            base_group_name = f"s{subject_id}" # e.g., "s4"
            subgroups = [
                "regent",
                "students",
                "professors",
                "edit_topics",
                "edit_questions",
                "view_question_bank",
                "add_students",
                "generate_exams",
                "view_grades",
                "auto_correct_exams"
            ]

            # Create each subgroup as a flat group with a hierarchical name
            subgroup_ids = {}
            for sub_name in subgroups:
                # Construct the full group name as it should be stored and looked up
                # This is the name Keycloak receives and stores internally.
                full_group_name = base_group_name + "/" + sub_name # e.g., "s4/regent"
                logger.debug(f"Attempting to create subgroup: {full_group_name}")

                # Create the group directly with its full hierarchical name segment
                subgroup_id = await loop.run_in_executor(
                    None,
                    lambda name=full_group_name: self.admin_client.create_group({"name": name})
                    # Note: We are NOT using a 'parent' argument here.
                    # Groups are created flat but with names that imply hierarchy.
                )
                logger.info(f"Created subgroup: {full_group_name} with ID: {subgroup_id}")
                # Store the ID using the *exact* name Keycloak received
                subgroup_ids[full_group_name] = subgroup_id # e.g., store as {"s4/regent": "id123"}

            # Verify the regent user exists before adding them to the group
            logger.info(f"Verifying regent user exists: {regent_keycloak_id}")
            regent_user_info = await loop.run_in_executor(
                None,
                lambda: self.admin_client.get_user(regent_keycloak_id)
            )
            regent_username = regent_user_info.get('username')
            logger.info(f"Regent user verified: {regent_username} (ID: {regent_keycloak_id})")

            # Find the specific regent subgroup ID
            # Use the *same* name format used when storing in subgroup_ids: "s{subject_id}/regent"
            # DO NOT add a leading slash here if the stored key doesn't have one.
            regent_group_name = f"{base_group_name}/regent" # e.g., "s4/regent"
            regent_group_id = subgroup_ids.get(regent_group_name) # This should now find "s4/regent"

            if not regent_group_id:
                 logger.error(f"Regent group {regent_group_name} not found after creation.")
                 logger.debug(f"Available group names in cache: {list(subgroup_ids.keys())}") # Add this line for debugging
                 return False # Or raise an error

            # Add the user to the s{subject_id}/regent group (Keycloak path will be /{regent_group_name})
            await loop.run_in_executor(
                None,
                lambda uid=regent_keycloak_id, gid=regent_group_id: self.admin_client.group_user_add(uid, gid)
            )
            logger.info(f"User {regent_username} (ID: {regent_keycloak_id}) added to group {regent_group_name} (ID: {regent_group_id})")

            logger.info(f"All groups for subject {subject_id} created and regent assigned successfully.")
            return True

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Keycloak Admin API error during group creation/assignment: {error_msg}")
            logger.exception(e) # Log the full traceback
            # Handle specific errors like user not found, group already exists, etc.
            if "User not found" in error_msg:
                 raise ValueError(f"Regent user with ID '{regent_keycloak_id}' not found in Keycloak.")
            # Re-raise or return False based on how you want to handle errors in the endpoint
            raise e # Re-raise to be handled by the endpoint

    async def update_subject_regent(self, subject_id: str, new_regent_id: str) -> bool:
        """
        Removes existing members from the subject's regent group and adds the new regent.
        """
        group_path = f"s{subject_id}/regent"
        logger.info(f"Updating regent for group {group_path} to user {new_regent_id}")
        
        try:
            loop = asyncio.get_event_loop()
            
            # 1. Find the group ID
            # get_group_by_path returns the group object or raises error if not found
            # Note: Depending on python-keycloak version, we might need to search for it if get_group_by_path isn't available
            # We will use a safe search approach:
            group_id = None
            groups = await loop.run_in_executor(None, lambda: self.admin_client.get_groups())
            
            # This is a naive search. For production with thousands of groups, use search params.
            # Since our groups are flat "s{id}/regent", we search for that name.
            for g in groups:
                if g['name'] == group_path:
                    group_id = g['id']
                    break
            
            if not group_id:
                logger.error(f"Group {group_path} not found.")
                return False

            # 2. Remove existing members (The old regent)
            members = await loop.run_in_executor(
                None, 
                lambda: self.admin_client.get_group_members(group_id)
            )
            
            for member in members:
                logger.info(f"Removing old regent {member['username']} from group {group_path}")
                await loop.run_in_executor(
                    None,
                    lambda uid=member['id']: self.admin_client.group_user_remove(uid, group_id)
                )

            # 3. Add new regent
            await loop.run_in_executor(
                None,
                lambda: self.admin_client.group_user_add(new_regent_id, group_id)
            )
            
            logger.info(f"New regent {new_regent_id} assigned successfully.")
            return True

        except Exception as e:
            logger.error(f"Failed to update regent: {e}")
            logger.exception(e)
            return False

    async def delete_subject_groups(self, subject_id: str) -> bool:
        """
        Deletes all Keycloak groups associated with a subject.
        """
        logger.info(f"Deleting groups for subject ID: {subject_id}")
        
        # Must match the list used in creation
        base_group_name = f"s{subject_id}"
        subgroups = [
            "regent", "students", "professors", "edit_topics", 
            "edit_questions", "view_question_bank", "add_students", 
            "generate_exams", "view_grades", "auto_correct_exams"
        ]
        
        try:
            loop = asyncio.get_event_loop()
            
            # Get all groups once to map names to IDs
            all_groups = await loop.run_in_executor(None, lambda: self.admin_client.get_groups())
            group_map = {g['name']: g['id'] for g in all_groups}

            for sub in subgroups:
                full_name = f"{base_group_name}/{sub}"
                group_id = group_map.get(full_name)
                
                if group_id:
                    logger.info(f"Deleting group: {full_name} (ID: {group_id})")
                    await loop.run_in_executor(
                        None,
                        lambda gid=group_id: self.admin_client.delete_group(gid)
                    )
                else:
                    logger.warning(f"Group {full_name} not found during deletion cleanup.")
            
            return True

        except Exception as e:
            logger.error(f"Error deleting subject groups: {e}")
            return False

    async def _get_group_id_by_name(self, group_name: str) -> str | None:
        """Helper to find a group ID by its flat name (e.g., 's1/students')"""
        loop = asyncio.get_event_loop()
        groups = await loop.run_in_executor(None, lambda: self.admin_client.get_groups())
        for g in groups:
            if g['name'] == group_name:
                return g['id']
        return None

    async def get_subject_students(self, subject_id: str) -> list[dict]:
        """Fetch all users in the subject's student group"""
        group_name = f"s{subject_id}/students"
        try:
            group_id = await self._get_group_id_by_name(group_name)
            if not group_id:
                logger.warning(f"Group {group_name} not found.")
                return []

            loop = asyncio.get_event_loop()
            members = await loop.run_in_executor(
                None, 
                lambda: self.admin_client.get_group_members(group_id)
            )
            return members
        except Exception as e:
            logger.error(f"Failed to fetch students for subject {subject_id}: {e}")
            return []

    async def add_students_to_subject(self, subject_id: str, student_ids: list[str]) -> None:
        """Add a list of users to the subject's student group"""
        group_name = f"s{subject_id}/students"
        try:
            group_id = await self._get_group_id_by_name(group_name)
            if not group_id:
                raise ValueError(f"Group {group_name} does not exist.")

            loop = asyncio.get_event_loop()
            for user_id in student_ids:
                try:
                    await loop.run_in_executor(
                        None,
                        lambda uid=user_id: self.admin_client.group_user_add(uid, group_id)
                    )
                    logger.info(f"Added user {user_id} to {group_name}")
                except Exception as e:
                    logger.error(f"Failed to add user {user_id} to group: {e}")
                    # Continue adding others even if one fails
        except Exception as e:
            logger.error(f"Error in add_students_to_subject: {e}")
            raise e


    async def manage_professor_permissions(
        self, 
        subject_id: str, 
        professor_id: str, 
        permissions: dict[str, bool]
    ) -> bool:
        """
        Adds/Removes user from permission subgroups based on the boolean dict.
        Also ensures user is added to the base 'professors' group.
        """
        base_group = f"s{subject_id}"
        professors_group_name = f"{base_group}/professors"
        
        # Valid permission subgroups mapping (DTO field name -> Group suffix)
        # In your case, they are identical, but mapping ensures safety.
        permission_map = {
            "edit_topics": "edit_topics",
            "edit_questions": "edit_questions",
            "view_question_bank": "view_question_bank",
            "add_students": "add_students",
            "generate_exams": "generate_exams",
            "view_grades": "view_grades",
            "auto_correct_exams": "auto_correct_exams"
        }

        try:
            loop = asyncio.get_event_loop()
            
            # 1. Fetch all groups to get IDs efficiently
            # We fetch all because we might need to touch 8 different groups
            all_groups = await loop.run_in_executor(None, lambda: self.admin_client.get_groups())
            
            # Create a lookup: {"s1/professors": "id_123", "s1/edit_topics": "id_456"}
            group_id_map = {}
            # Flatten the structure if needed, or just find by name
            # Assuming flat structure as per your setup
            for g in all_groups:
                group_id_map[g['name']] = g['id']

            # 2. Always ensure user is in the base 'professors' group
            prof_group_id = group_id_map.get(professors_group_name)
            if prof_group_id:
                try:
                    await loop.run_in_executor(
                        None, 
                        lambda: self.admin_client.group_user_add(professor_id, prof_group_id)
                    )
                except Exception:
                    pass # User likely already in group, ignore

            # 3. Iterate permissions and Add/Remove
            for perm_key, is_active in permissions.items():
                suffix = permission_map.get(perm_key)
                if not suffix: 
                    continue # Skip unknown keys
                
                full_group_name = f"{base_group}/{suffix}"
                group_id = group_id_map.get(full_group_name)
                
                if not group_id:
                    logger.warning(f"Group {full_group_name} not found in Keycloak.")
                    continue

                if is_active:
                    # ADD to group
                    try:
                        await loop.run_in_executor(
                            None, 
                            lambda uid=professor_id, gid=group_id: self.admin_client.group_user_add(uid, gid)
                        )
                        logger.info(f"Added {professor_id} to {full_group_name}")
                    except Exception:
                        pass # Ignore if already member
                else:
                    # REMOVE from group
                    try:
                        await loop.run_in_executor(
                            None, 
                            lambda uid=professor_id, gid=group_id: self.admin_client.group_user_remove(uid, gid)
                        )
                        logger.info(f"Removed {professor_id} from {full_group_name}")
                    except Exception:
                        pass # Ignore if not a member

            return True

        except Exception as e:
            logger.error(f"Error managing professor permissions: {e}")
            raise e

    async def remove_professor_from_subject(self, subject_id: str, professor_id: str) -> bool:
        """
        Removes a professor from the 'professors' group AND all permission subgroups.
        """
        base_group = f"s{subject_id}"
        # List of all possible groups a professor might be in
        subgroups = [
            "professors", # Base group
            "edit_topics", "edit_questions", "view_question_bank", 
            "add_students", "generate_exams", "view_grades", 
            "auto_correct_exams"
        ]

        try:
            loop = asyncio.get_event_loop()
            all_groups = await loop.run_in_executor(None, lambda: self.admin_client.get_groups())
            group_id_map = {g['name']: g['id'] for g in all_groups}

            for sub in subgroups:
                full_name = f"{base_group}/{sub}"
                group_id = group_id_map.get(full_name)
                
                if group_id:
                    try:
                        await loop.run_in_executor(
                            None,
                            lambda uid=professor_id, gid=group_id: self.admin_client.group_user_remove(uid, gid)
                        )
                    except Exception:
                        pass # Ignore if user wasn't in that specific subgroup

            logger.info(f"Professor {professor_id} removed from all groups for subject {subject_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing professor: {e}")
            return False


keycloak_client = KeycloakClient()

"""

            self.admin_client = KeycloakAdmin(
                server_url=settings.KEYCLOAK_SERVER_URL,
                username=
                password=
                realm_name='EduPro'
                user_realm_name="master"
                verify=True
            )

"""