import { Button } from '@/components/ui/button'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: Index,
})

function Index() {
  return (
    <div className="min-h-screen bg-gray-50 px-20 py-16">
      {/* Heading */}
      <h1 className="text-5xl font-semibold text-center mb-20">Bem-vind@ ao EduPro</h1>

      {/* Two-column layout */}
      <div className="flex items-start justify-center gap-24">
        {/* Left column */}
        <div className="flex flex-col items-center space-y-10 max-w-md text-center">
          <p className="text-2xl text-gray-700 leading-snug">
            Um sistema que gera e avalia <br/> unidades curriculares
          </p>

          <Button className="h-16.5 w-67.5 px-10 py-4 text-xl">Log In</Button>

          <p className="text-lg text-gray-600">
            Ainda não tens conta?{' '}
            <a href="#" className="text-sky-600 hover:underline">
              Cria uma nova
            </a>
          </p>
        </div>

        {/* Right column (logo) */}
        <div>
          <img
            src="/logo.png"
            alt="EduPro logo"
            className="h-auto w-156.5 h-89.5"
          />
        </div>
      </div>
    </div>
  )
}
