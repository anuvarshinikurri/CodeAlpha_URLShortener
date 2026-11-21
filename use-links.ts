import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";

export const linksQueryKey = ["links"] as const;

export function useLinks() {
  return useQuery({ queryKey: linksQueryKey, queryFn: api.list, retry: 1 });
}

export function useShortenLink() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.shorten,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: linksQueryKey }),
  });
}

export function useDeleteLink() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.remove,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: linksQueryKey }),
  });
}
