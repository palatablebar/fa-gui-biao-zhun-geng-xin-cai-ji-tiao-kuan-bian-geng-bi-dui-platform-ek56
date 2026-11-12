import http from './http'
import type { User } from '../types/user'

export interface LoginResult {
  access_token: string
  token: string
  user: User
}

export async function login(email: string, password: string): Promise<LoginResult> {
  const { data } = await http.post('/auth/login', { email, password })
  return data
}

export async function fetchMe(): Promise<{ user: User }> {
  const { data } = await http.get('/auth/me')
  return data
}
