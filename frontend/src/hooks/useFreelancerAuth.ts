/**
 * Authentication hook for freelancer portal.
 *
 * Uses a separate token from admin auth to ensure complete isolation.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"

import {
  FreelancerAuthService,
  type FreelancerPublicMe,
  type FreelancerRegister,
  isFreelancerLoggedIn,
  removeFreelancerToken,
  setFreelancerToken,
} from "@/client/freelancerPortalService"

// Re-export for convenience
export { isFreelancerLoggedIn }

/**
 * Hook for freelancer authentication
 */
const useFreelancerAuth = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Get current freelancer profile
  const { data: freelancer, isLoading: isLoadingFreelancer } = useQuery<
    FreelancerPublicMe | null
  >({
    queryKey: ["currentFreelancer"],
    queryFn: async () => {
      if (!isFreelancerLoggedIn()) return null
      try {
        return await FreelancerAuthService.getMe()
      } catch {
        // Token invalid, clear it
        removeFreelancerToken()
        return null
      }
    },
    enabled: isFreelancerLoggedIn(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: async (data: { username: string; password: string }) => {
      const response = await FreelancerAuthService.login(data)
      setFreelancerToken(response.access_token)
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["currentFreelancer"] })
      navigate({ to: "/freelancer" } as any)
    },
  })

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: async (data: FreelancerRegister) => {
      return await FreelancerAuthService.register(data)
    },
    onSuccess: () => {
      navigate({ to: "/freelancer/login" } as any)
    },
  })

  // Logout function
  const logout = () => {
    removeFreelancerToken()
    queryClient.removeQueries({ queryKey: ["currentFreelancer"] })
    queryClient.removeQueries({ queryKey: ["freelancer"] })
    navigate({ to: "/freelancer/login" } as any)
  }

  // Reset login state (for error recovery)
  const resetLoginState = () => {
    removeFreelancerToken()
    queryClient.removeQueries({ queryKey: ["currentFreelancer"] })
  }

  return {
    freelancer,
    isLoadingFreelancer,
    isAuthenticated: isFreelancerLoggedIn() && !!freelancer,
    loginMutation,
    registerMutation,
    logout,
    resetLoginState,
  }
}

export default useFreelancerAuth
