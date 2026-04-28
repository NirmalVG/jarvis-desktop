"""
Jarvis Next.js Expertise Module
Comprehensive knowledge and coding capabilities for Next.js development.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import re


@dataclass
class NextJSProjectTemplate:
    name: str
    description: str
    dependencies: Dict[str, str]
    files: Dict[str, str]
    setup_commands: List[str]


class NextJSExpertise:
    """Comprehensive Next.js knowledge and coding expertise."""
    
    def __init__(self):
        self.templates = self._build_templates()
        self.best_practices = self._build_best_practices()
        self.common_patterns = self._build_common_patterns()
    
    def _build_templates(self) -> Dict[str, NextJSProjectTemplate]:
        """Build Next.js project templates."""
        
        return {
            "fullstack_app": NextJSProjectTemplate(
                name="Full-Stack Next.js App",
                description="Complete full-stack application with authentication, database, and API routes",
                dependencies={
                    "next": "^14.0.0",
                    "react": "^18.0.0",
                    "react-dom": "^18.0.0",
                    "typescript": "^5.0.0",
                    "@types/node": "^20.0.0",
                    "@types/react": "^18.0.0",
                    "@types/react-dom": "^18.0.0",
                    "tailwindcss": "^3.3.0",
                    "autoprefixer": "^10.4.0",
                    "postcss": "^8.4.0",
                    "prisma": "^5.0.0",
                    "@prisma/client": "^5.0.0",
                    "next-auth": "^4.24.0",
                    "bcryptjs": "^2.4.3",
                    "@types/bcryptjs": "^2.4.6",
                    "lucide-react": "^0.294.0",
                    "clsx": "^2.0.0",
                    "tailwind-merge": "^2.0.0"
                },
                files={
                    "package.json": '''{
  "name": "my-nextjs-app",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "db:push": "prisma db push",
    "db:studio": "prisma studio"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "typescript": "^5.0.0",
    "@types/node": "^20.0.0",
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "prisma": "^5.0.0",
    "@prisma/client": "^5.0.0",
    "next-auth": "^4.24.0",
    "bcryptjs": "^2.4.3",
    "@types/bcryptjs": "^2.4.6",
    "lucide-react": "^0.294.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0"
  },
  "devDependencies": {
    "eslint": "^8.0.0",
    "eslint-config-next": "^14.0.0"
  }
}''',
                    "next.config.js": '''/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  images: {
    domains: ['localhost'],
  },
}

module.exports = nextConfig''',
                    "tailwind.config.js": '''/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
}''',
                    "app/layout.tsx": '''import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'My Next.js App',
  description: 'A full-stack Next.js application',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}''',
                    "app/page.tsx": '''export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <h1 className="text-4xl font-bold">
          Welcome to Your Next.js App
        </h1>
      </div>
    </main>
  )
}''',
                    "lib/utils.ts": '''import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}''',
                    "components/ui/button.tsx": '''import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline:
          "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }''',
                    "prisma/schema.prisma": '''// This is your Prisma schema file,
// learn more about it in the docs: https://pris.ly/d/prisma-schema

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "sqlite"
  url      = env("DATABASE_URL")
}

model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  name      String?
  password  String
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}''',
                    ".env.local": '''# Database
DATABASE_URL="file:./dev.db"

# NextAuth
NEXTAUTH_URL="http://localhost:3000"
NEXTAUTH_SECRET="your-secret-key-here"'''
                },
                setup_commands=[
                    "npx create-next-app@latest my-app --typescript --tailwind --eslint",
                    "cd my-app",
                    "npm install prisma @prisma/client next-auth bcryptjs @types/bcryptjs lucide-react clsx tailwind-merge",
                    "npm install -D @types/node @types/react @types/react-dom",
                    "npx prisma init",
                    "npx prisma db push"
                ]
            ),
            
            "api_service": NextJSProjectTemplate(
                name="API Service with Next.js",
                description="Headless API service using Next.js App Router",
                dependencies={
                    "next": "^14.0.0",
                    "react": "^18.0.0",
                    "react-dom": "^18.0.0",
                    "typescript": "^5.0.0",
                    "@types/node": "^20.0.0",
                    "zod": "^3.22.0",
                    "jsonwebtoken": "^9.0.0",
                    "@types/jsonwebtoken": "^9.0.0",
                    "bcryptjs": "^2.4.3",
                    "@types/bcryptjs": "^2.4.6"
                },
                files={
                    "app/api/users/route.ts": '''import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const createUserSchema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
})

export async function GET(request: NextRequest) {
  // Fetch users from database
  const users = [
    { id: 1, name: 'John Doe', email: 'john@example.com' },
    { id: 2, name: 'Jane Smith', email: 'jane@example.com' },
  ]
  
  return NextResponse.json({ users })
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const validatedData = createUserSchema.parse(body)
    
    // Create user in database
    const newUser = {
      id: Date.now(),
      ...validatedData,
    }
    
    return NextResponse.json({ user: newUser }, { status: 201 })
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Validation failed', details: error.errors },
        { status: 400 }
      )
    }
    
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}''',
                    "lib/validation.ts": '''import { z } from 'zod'

export const CreateUserSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
})

export type CreateUserInput = z.infer<typeof CreateUserSchema>''',
                    "middleware.ts": '''import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  // Add CORS headers
  const response = NextResponse.next()
  
  response.headers.set('Access-Control-Allow-Origin', '*')
  response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
  response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization')
  
  return response
}

export const config = {
  matcher: '/api/:path*',
}'''
                },
                setup_commands=[
                    "npx create-next-app@latest my-api --typescript --eslint --app",
                    "cd my-api",
                    "npm install zod jsonwebtoken @types/jsonwebtoken bcryptjs @types/bcryptjs"
                ]
            )
        }
    
    def _build_best_practices(self) -> Dict[str, List[str]]:
        """Build Next.js best practices knowledge base."""
        
        return {
            "performance": [
                "Use Image component for optimized images",
                "Implement dynamic imports for code splitting",
                "Use getStaticProps and getServerProps appropriately",
                "Optimize bundle size with dynamic imports",
                "Use React.memo and useMemo for component optimization",
                "Implement proper caching strategies",
                "Use Next.js Analytics for performance monitoring"
            ],
            "security": [
                "Validate all input data with Zod schemas",
                "Implement proper authentication with NextAuth.js",
                "Use environment variables for sensitive data",
                "Implement CSRF protection",
                "Secure API routes with proper middleware",
                "Use HTTPS in production",
                "Implement proper error handling without exposing sensitive info"
            ],
            "architecture": [
                "Follow App Router conventions for Next.js 13+",
                "Separate components, hooks, and utilities",
                "Use TypeScript for type safety",
                "Implement proper error boundaries",
                "Use Server Components for data fetching",
                "Use Client Components sparingly for interactivity",
                "Organize routes logically"
            ],
            "seo": [
                "Use metadata API for page titles and descriptions",
                "Implement structured data with JSON-LD",
                "Use semantic HTML elements",
                "Optimize images with alt text",
                "Implement proper URL structure",
                "Use sitemap.xml and robots.txt",
                "Implement Open Graph and Twitter Card meta tags"
            ]
        }
    
    def _build_common_patterns(self) -> Dict[str, str]:
        """Build common Next.js patterns and code examples."""
        
        return {
            "auth_middleware": '''import { withAuth } from "next-auth/middleware"

export default withAuth(
  function middleware(req) {
    // Additional middleware logic
  },
  {
    callbacks: {
      authorized: ({ token }) => !!token
    },
  }
)

export const config = {
  matcher: ["/dashboard/:path*", "/profile/:path*"]
}''',
            
            "api_error_handling": '''import { NextResponse } from 'next/server'

export class APIError extends Error {
  constructor(
    message: string,
    public statusCode: number = 500,
    public code?: string
  ) {
    super(message)
    this.name = 'APIError'
  }
}

export function handleAPIError(error: unknown) {
  console.error('API Error:', error)
  
  if (error instanceof APIError) {
    return NextResponse.json(
      { error: error.message, code: error.code },
      { status: error.statusCode }
    )
  }
  
  return NextResponse.json(
    { error: 'Internal server error' },
    { status: 500 }
  )
}''',
            
            "data_fetching": '''// Server Component - Data Fetching
async function getUserData(id: string) {
  const res = await fetch(`https://api.example.com/users/${id}`, {
    cache: 'force-cache', // or 'no-store' for dynamic data
    next: { revalidate: 60 } // Revalidate every 60 seconds
  })
  
  if (!res.ok) {
    throw new Error('Failed to fetch user data')
  }
  
  return res.json()
}

export default async function UserProfile({ params }: { params: { id: string } }) {
  const user = await getUserData(params.id)
  
  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.email}</p>
    </div>
  )
}''',
            
            "form_handling": ''''use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function ContactForm() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    message: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      const response = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        router.push('/thank-you')
      } else {
        throw new Error('Failed to submit form')
      }
    } catch (error) {
      console.error('Form submission error:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Submitting...' : 'Submit'}
      </button>
    </form>
  )
}''',
            
            "custom_hooks": ''''use client'

import { useState, useEffect } from 'react'

interface UseFetchResult<T> {
  data: T | null
  loading: boolean
  error: string | null
  refetch: () => void
}

export function useFetch<T>(url: string): UseFetchResult<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      const response = await fetch(url)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [url])

  return { data, loading, error, refetch: fetchData }
}''',
            
            "server_actions": ''''use client'

import { createUser } from '@/app/actions/user'

export default function CreateUserForm() {
  async function handleSubmit(formData: FormData) {
    'use server'
    
    const name = formData.get('name') as string
    const email = formData.get('email') as string
    
    try {
      await createUser({ name, email })
      return { success: true, message: 'User created successfully' }
    } catch (error) {
      return { success: false, message: 'Failed to create user' }
    }
  }

  return (
    <form action={handleSubmit}>
      <input name="name" placeholder="Name" required />
      <input name="email" type="email" placeholder="Email" required />
      <button type="submit">Create User</button>
    </form>
  )
}'''
        }
    
    def get_template(self, template_name: str) -> Optional[NextJSProjectTemplate]:
        """Get a specific project template."""
        return self.templates.get(template_name)
    
    def get_best_practices(self, category: str) -> List[str]:
        """Get best practices for a specific category."""
        return self.best_practices.get(category, [])
    
    def get_pattern(self, pattern_name: str) -> Optional[str]:
        """Get a specific code pattern."""
        return self.common_patterns.get(pattern_name)
    
    def list_templates(self) -> List[str]:
        """List all available templates."""
        return list(self.templates.keys())
    
    def list_patterns(self) -> List[str]:
        """List all available patterns."""
        return list(self.common_patterns.keys())


# Singleton instance
nextjs_expertise = NextJSExpertise()
