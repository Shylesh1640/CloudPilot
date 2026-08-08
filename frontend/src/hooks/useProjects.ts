import { useCallback, useEffect, useState } from 'react';
import { projectService } from '@/services/projectService';
import type { CreateProjectPayload, Project, UpdateProjectPayload } from '@/types';

/**
 * Hook for managing the authenticated user's projects.
 * Handles loading, error, and CRUD operations.
 */
export function useProjects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProjects = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await projectService.list();
      setProjects(data);
    } catch (err) {
      setError('Failed to load projects.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const createProject = useCallback(
    async (payload: CreateProjectPayload): Promise<Project> => {
      const project = await projectService.create(payload);
      setProjects((prev) => [project, ...prev]);
      return project;
    },
    []
  );

  const updateProject = useCallback(
    async (id: string, payload: UpdateProjectPayload): Promise<Project> => {
      const updated = await projectService.update(id, payload);
      setProjects((prev) => prev.map((p) => (p.id === id ? updated : p)));
      return updated;
    },
    []
  );

  const deleteProject = useCallback(async (id: string): Promise<void> => {
    await projectService.delete(id);
    setProjects((prev) => prev.filter((p) => p.id !== id));
  }, []);

  return {
    projects,
    isLoading,
    error,
    refetch: fetchProjects,
    createProject,
    updateProject,
    deleteProject,
  };
}
