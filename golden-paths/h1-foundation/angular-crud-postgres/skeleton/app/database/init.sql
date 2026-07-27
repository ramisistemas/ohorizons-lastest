-- Esquema de ejemplo para el CRUD + configuración de roles PostgREST.

create table if not exists public.tasks (
    id bigint generated always as identity primary key,
    title text not null,
    notes text,
    done boolean not null default false,
    created_at timestamptz not null default now()
);

-- Rol anónimo que usa PostgREST cuando no hay JWT (demo sin auth).
-- En producción reemplaza esto por roles con permisos acotados por tabla/columna.
do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'web_anon') then
    create role web_anon nologin;
  end if;
end
$$;

grant usage on schema public to web_anon;
grant select, insert, update, delete on public.tasks to web_anon;
grant usage, select on sequence public.tasks_id_seq to web_anon;
