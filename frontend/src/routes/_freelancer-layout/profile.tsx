import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Suspense } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { FreelancerAuthService } from "@/client/freelancerPortalService"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import useCustomToast from "@/hooks/useCustomToast"
import useFreelancerAuth from "@/hooks/useFreelancerAuth"

export const Route = (createFileRoute as any)("/_freelancer-layout/profile")({
  component: FreelancerProfile,
  head: () => ({
    meta: [{ title: "Profile - Freelancer Portal" }],
  }),
})

// Profile update schema
const profileSchema = z.object({
  name: z.string().min(1, "Name is required"),
  hourly_rate: z.string().min(1, "Hourly rate is required"),
})

type ProfileForm = z.infer<typeof profileSchema>

// Password update schema
const passwordSchema = z
  .object({
    current_password: z.string().min(8, "Password must be at least 8 characters"),
    new_password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: z.string().min(8, "Please confirm your password"),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords don't match",
    path: ["confirm_password"],
  })

type PasswordForm = z.infer<typeof passwordSchema>

function ProfileSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-48" />
      <Skeleton className="h-48" />
    </div>
  )
}

function ProfileContent() {
  const queryClient = useQueryClient()
  const { freelancer } = useFreelancerAuth()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  // Profile form
  const profileForm = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      name: freelancer?.name || "",
      hourly_rate: freelancer?.hourly_rate || "50.00",
    },
  })

  // Password form
  const passwordForm = useForm<PasswordForm>({
    resolver: zodResolver(passwordSchema),
    defaultValues: {
      current_password: "",
      new_password: "",
      confirm_password: "",
    },
  })

  // Profile update mutation
  const profileMutation = useMutation({
    mutationFn: (data: ProfileForm) => FreelancerAuthService.updateMe(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["currentFreelancer"] })
      showSuccessToast("Profile updated successfully")
    },
    onError: (error: any) => {
      showErrorToast(error?.body?.detail || "Failed to update profile")
    },
  })

  // Password update mutation
  const passwordMutation = useMutation({
    mutationFn: (data: PasswordForm) =>
      FreelancerAuthService.updatePassword({
        current_password: data.current_password,
        new_password: data.new_password,
      }),
    onSuccess: () => {
      passwordForm.reset()
      showSuccessToast("Password updated successfully")
    },
    onError: (error: any) => {
      showErrorToast(error?.body?.detail || "Failed to update password")
    },
  })

  const onProfileSubmit = (data: ProfileForm) => {
    profileMutation.mutate(data)
  }

  const onPasswordSubmit = (data: PasswordForm) => {
    passwordMutation.mutate(data)
  }

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Profile Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Profile Settings</CardTitle>
          <CardDescription>
            Update your personal information and hourly rate
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...profileForm}>
            <form
              onSubmit={profileForm.handleSubmit(onProfileSubmit)}
              className="space-y-4"
            >
              <FormField
                control={profileForm.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Full Name</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input value={freelancer?.email || ""} disabled />
                </FormControl>
                <FormDescription>
                  Email cannot be changed at this time
                </FormDescription>
              </FormItem>

              <FormField
                control={profileForm.control}
                name="hourly_rate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Hourly Rate (USD)</FormLabel>
                    <FormControl>
                      <Input type="number" step="0.01" min="0" {...field} />
                    </FormControl>
                    <FormDescription>
                      Your default hourly rate for new work
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <Button type="submit" disabled={profileMutation.isPending}>
                {profileMutation.isPending ? "Saving..." : "Save Changes"}
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>

      <Separator />

      {/* Password Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Change Password</CardTitle>
          <CardDescription>
            Update your password to keep your account secure
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...passwordForm}>
            <form
              onSubmit={passwordForm.handleSubmit(onPasswordSubmit)}
              className="space-y-4"
            >
              <FormField
                control={passwordForm.control}
                name="current_password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Current Password</FormLabel>
                    <FormControl>
                      <Input type="password" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={passwordForm.control}
                name="new_password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>New Password</FormLabel>
                    <FormControl>
                      <Input type="password" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={passwordForm.control}
                name="confirm_password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Confirm New Password</FormLabel>
                    <FormControl>
                      <Input type="password" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <Button type="submit" disabled={passwordMutation.isPending}>
                {passwordMutation.isPending ? "Updating..." : "Update Password"}
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  )
}

function FreelancerProfile() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Profile</h1>
        <p className="text-muted-foreground">
          Manage your account settings
        </p>
      </div>
      <Suspense fallback={<ProfileSkeleton />}>
        <ProfileContent />
      </Suspense>
    </div>
  )
}
