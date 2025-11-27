# src/routers/subject.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.models.subject import Subject, SubjectCreateRequest, SubjectCreateResponse
from src.core.db import get_session
from src.core.deps import require_manager, verify_regent_exists # Import the new dependency
from src.core.keycloak import keycloak_client
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=SubjectCreateResponse, dependencies=[Depends(require_manager)])
async def create_subject_endpoint(
    subject_data: SubjectCreateRequest, # Receive the request body data
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new subject in the database and its corresponding Keycloak groups.
    Assigns the specified user as the regent.
    Requires the 'manager' role.
    """
    logger.info(f"Manager is attempting to create a new subject: '{subject_data.name}', assigning regent ID: {subject_data.regent_keycloak_id}")

    try:
        # 1. Verify regent exists BEFORE creating anything in the database
        # Call the verification function explicitly here, now that we have subject_data
        regent_info = await verify_regent_exists(subject_data.regent_keycloak_id)

        # 2. Create the Subject in the local database
        db_subject = Subject(name=subject_data.name)
        session.add(db_subject)
        await session.commit()
        await session.refresh(db_subject) # Get the auto-generated ID

        logger.info(f"Subject '{db_subject.name}' created in database with ID: {db_subject.id}")

        # 3. Create Keycloak groups and assign regent using the ID from the database
        success = await keycloak_client.create_subject_groups_and_assign_regent(
            subject_id=str(db_subject.id), # Use the DB ID to name the groups
            regent_keycloak_id=subject_data.regent_keycloak_id
        )

        if not success:
            # If group creation/assignment failed, consider rolling back the DB creation
            # For now, just log and raise an error
            logger.error(f"Failed to create Keycloak groups for subject {db_subject.id}. DB entry may need cleanup.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Subject created in database, but failed to create Keycloak groups."
            )

        logger.info(f"Subject '{db_subject.name}' (ID: {db_subject.id}) and Keycloak groups created successfully. Regent assigned.")

        # Return success response
        return SubjectCreateResponse(
            id=db_subject.id,
            name=db_subject.name,
            message="Subject and Keycloak groups created successfully. Regent assigned.",
            regent_username=regent_info.get('username') # Return the verified regent's username
        )

    except ValueError as ve:
        # Handle specific validation errors like regent not found (caught by verify_regent_exists)
        logger.warning(f"Validation error during subject creation: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        # Handle other errors during creation (e.g., DB error, Keycloak error)
        logger.error(f"Failed to create subject '{subject_data.name}': {e}")
        logger.exception(e) # Log the full traceback
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the subject in the database or Keycloak."
        )

# ... (keep existing endpoints like GET, PUT, etc.) ...