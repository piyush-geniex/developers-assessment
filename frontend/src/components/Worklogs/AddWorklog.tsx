import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import axios from "axios"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const formSchema = z.object({
  freelancer_id: z.string().min(1, { message: "Freelancer is required" }),
  item_id: z.string().min(1, { message: "Item is required" }),
  hours: z.string().min(1, { message: "Hours is required" }),
})

type FormData = z.infer<typeof formSchema>

const AddWorklog = () => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      freelancer_id: "",
      item_id: "",
      hours: "",
    },
  })

  const { data: freelancersData, isLoading: loadingFreelancers } = useQuery({
    queryKey: ["freelancers"],
    queryFn: async () => {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000"
      const token = localStorage.getItem("access_token")
      const response = await axios.get(`${apiUrl}/api/v1/worklogs/freelancers`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      return response.data
    },
    enabled: isOpen,
  })

  const { data: itemsData, isLoading: loadingItems } = useQuery({
    queryKey: ["items"],
    queryFn: async () => {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000"
      const token = localStorage.getItem("access_token")
      const response = await axios.get(`${apiUrl}/api/v1/items/`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      return response.data
    },
    enabled: isOpen,
  })

  const freelancers = freelancersData?.data || []
  const items = itemsData?.data || []

  const mutation = useMutation({
    mutationFn: async (data: FormData) => {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000"
      const token = localStorage.getItem("access_token")

      const selectedItem = items.find((itm: any) => itm.id === data.item_id)
      const itemTitle = selectedItem?.title || ""

      const response = await axios.post(
        `${apiUrl}/api/v1/worklogs/`,
        {
          freelancer_id: data.freelancer_id,
          item_id: data.item_id,
          item_title: itemTitle,
          hours: parseFloat(data.hours),
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      )
      return response.data
    },
    onSuccess: () => {
      showSuccessToast("Worklog created successfully")
      form.reset()
      setIsOpen(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["worklogs"] })
    },
  })

  const onSubmit = (data: FormData) => {
    mutation.mutate(data)
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button aria-label="Add new worklog">
          <Plus />
          Add Worklog
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add Worklog</DialogTitle>
          <DialogDescription>
            Fill in the details to create a new worklog.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <div className="grid gap-4 py-4">
              <FormField
                control={form.control}
                name="freelancer_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Freelancer <span className="text-destructive">*</span>
                    </FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                      disabled={loadingFreelancers}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a freelancer" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {freelancers.map((freelancer: any) => (
                          <SelectItem key={freelancer.id} value={freelancer.id}>
                            {freelancer.full_name} (${freelancer.hourly_rate}/hr)
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="item_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Item <span className="text-destructive">*</span>
                    </FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                      disabled={loadingItems}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select an item" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {items.map((item: any) => (
                          <SelectItem key={item.id} value={item.id}>
                            {item.title}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="hours"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Hours <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder="8.5"
                        type="number"
                        step="0.1"
                        min="0"
                        max="24"
                        {...field}
                        required
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline" disabled={mutation.isPending}>
                  Cancel
                </Button>
              </DialogClose>
              <LoadingButton type="submit" loading={mutation.isPending}>
                Save
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default AddWorklog
