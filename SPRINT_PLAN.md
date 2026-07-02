# Sprint Plan — Authentication & Database Connection

## Objective

Connect the system to a real Supabase PostgreSQL database, implement JWT-based authentication, seed sample data, and build a functional login flow on the frontend.

---

## Backend

### 1. Configure Supabase Credentials & Migrate

- Add real `DATABASE_URL` and `DIRECT_URL` to `.env` (from Supabase Dashboard → Settings → Database)
- Run `npx prisma migrate dev --name init` to create all tables on Supabase
- Verify connection works

### 2. Auth Module (JWT)

| Endpoint | Description |
|----------|-------------|
| `POST /auth/register` | Create user with hashed password, return JWT |
| `POST /auth/login` | Validate credentials, return JWT |

**Dependencies:** `@nestjs/jwt`, `@nestjs/passport`, `passport-jwt`, `bcrypt`

**Files to create:**
- `src/auth/auth.module.ts` — registers JwtModule, AuthService, JwtStrategy
- `src/auth/auth.service.ts` — register/login logic with bcrypt
- `src/auth/auth.controller.ts` — POST endpoints
- `src/auth/jwt.strategy.ts` — validates Bearer token
- `src/auth/jwt-auth.guard.ts` — reusable guard

### 3. Protect Routes

- Apply `JwtAuthGuard` to all CRUD endpoints (`/users`, `/cameras`, `/accidents`, `/alerts`)
- `/auth/login` and `/auth/register` remain public

### 4. Seed Script

Create `prisma/seed.ts`:
- 1 Admin user (email: admin@system.com, password: admin123)
- 1 Operator user (email: operator@system.com, password: operator123)
- 3–5 sample cameras with realistic Hanoi locations

### 5. Enable CORS

Add to `main.ts`:
```ts
app.enableCors({ origin: 'http://localhost:5173' });
```

---

## Frontend

### 6. Login Page

- Route: `/login`
- Form: email + password (Ant Design `Form` + `Input`)
- Calls `POST /auth/login`
- On success: store `access_token` in localStorage, redirect to `/dashboard`

### 7. Axios Interceptor

- Automatically attach `Authorization: Bearer <token>` to every request
- On 401 response: clear token, redirect to `/login`

### 8. Protected Routes

- Wrap all app routes (`/dashboard`, `/cameras`, `/accidents`, `/alerts`) with auth check
- If no token → redirect to `/login`
- If token exists → render layout normally

---

## Acceptance Criteria

- [ ] `prisma migrate dev` runs successfully against Supabase
- [ ] `POST /auth/register` creates user with hashed password, returns JWT
- [ ] `POST /auth/login` validates credentials, returns JWT
- [ ] Protected routes return `401 Unauthorized` without valid token
- [ ] Frontend login page authenticates and persists session
- [ ] Unauthenticated users are redirected to `/login`
- [ ] `npm run build` passes for both backend and frontend

---

## Risks & Blockers

| Risk | Mitigation |
|------|-----------|
| Supabase credentials not configured | Cannot migrate until real creds are provided |
| Prisma 7 breaking changes | Already resolved (schema + config format fixed) |
| CORS issues in dev | Explicitly whitelist `localhost:5173` |
