# Keycloak + FastAPI

The idea here is that we will demonstrate using Keycloak to assign users to groups.  Those groups will be related to roles, each role will have have associated scopes.  Keycloak will have clients that.

## Tutorial

Let's achieve the following:

- General user can only read Collections & Items
- Admin to CRUD actions and items
- Specific User can CRUD a specific collection's items, not collection itself

1. Create demo realm: `stac-api-playground`
2. Create users:
   - Bob represents a basic user
     - username: `bob`
     - first name: `Bob`
     - last name: `Basic`
   - Alice represents an admin
     - username: `alic`
     - first name: `Alice`
     - last name: `Admin`
3. Create realm roles:
   - A role to represent basic users
     - Role name: `Basic User`
   - A role to represent admins
     - Role name: `Admin`
4. Create a client:
   - General settings
     - client type: `OpenID Connect`
     - client id: `stac-api`
   - Capability config:
     - Client authentication: `Off`
   - Login settings:
     - Root URL: `http://localhost:8080`
     - Valid redirect URIs: `http://localhost:8080/*`
5. Create custom authorization scopes for the app.
   1. Under the client's Authorization tab, select "Scopes" (not to be confused with the "Client scopes" tab).
   1. Create the following authorization scopes:
      - `collection:create`
      - `collection:read`
      - `collection:update`
      - `collection:delete`
      - `item:create`
      - `item:read`
      - `item:update`
      - `item:delete`
6. Create client role policies. Think of these are individual tests that return whether the user is permitted to do _something_ (TODO: Describe that better) based on that user's associated roles.
   - `Is Admin` will tell us if a user is an admin
     - Policy Type: `Role`
     - Name: `Is Admins`
     - Roles: `Admin`
7. Create client resources. These are things we will want to protect.
   - Allow for both reading individual collections and listing collections. You'll note that we could have split that into two separate resources, however that is a use-case we don't need to build for on this project.
     - Name: `Collections - Read`
     - URIs:
       - `collections`
       - `collections/{id}`
     - Authorization scopes:
       - `collection:read`
   - Allow for both reading individual collections and listing collections. You'll note that we could have split that into two separate resources, however that is a use-case we don't need to build for on this project.
     - Name: `Collection - Create`
     - URIs:
       - `collections`
     - Authorization scopes:
       - `collection:create`
8. Create resource-based permission
   - We will establish that all users have read access to resources.
     - Name: `Read Permission`
     - Resources:
       - `Collections - Read`
     - Policies:
       - `Default Policy`
   - We will establish that only admins have write access to resources.
     - Name: `Write Permission`
     - Resources:
       - `Collections - Create`
     - Policies:
       - `Is Admin`

## TODO

- What's the difference between a "scope-based" permission and a "resource-based" permission?
- Client Authorization Scopes vs Client Scopes, what's the difference?
- What are "resource types" used for?
- It seems that the resource server must be private to make use of authorization.

1. Core Terms:

- [`role`](https://www.keycloak.org/docs/latest/server_admin/#core-concepts-and-terms)
  > Roles identify a type or category of user. `Admin`, `user`, `manager`, and `employee` are all typical roles that may exist in an organization. Applications often assign access and permissions to specific roles rather than individual users as dealing with users can be too fine-grained and hard to manage.
- [`user role mapping`](https://www.keycloak.org/docs/latest/server_admin/#core-concepts-and-terms)
  > A user role mapping defines a mapping between a role and a user. A user can be associated with zero or more roles. This role mapping information can be encapsulated into tokens and assertions so that applications can decide access permissions on various resources they manage.
- [`composite roles`](https://www.keycloak.org/docs/latest/server_admin/#core-concepts-and-terms)
  > A composite role is a role that can be associated with other roles. For example a `superuser` composite role could be associated with the `sales-admin` and `order-entry-admin` roles. If a user is mapped to the `superuser` role they also inherit the `sales-admin` and `order-entry-admin` roles.
- [`groups`](https://www.keycloak.org/docs/latest/server_admin/#core-concepts-and-terms)
  > Groups manage groups of users. Attributes can be defined for a group. You can map roles to a group as well. Users that become members of a group inherit the attributes and role mappings that group defines.
- [`realms`](https://www.keycloak.org/docs/latest/server_admin/#core-concepts-and-terms)
  > A realm manages a set of users, credentials, roles, and groups. A user belongs to and logs into a realm. Realms are isolated from one another and can only manage and authenticate the users that they control.
- [`clients`](https://www.keycloak.org/docs/latest/server_admin/#core-concepts-and-terms)
  > Clients are entities that can request Keycloak to authenticate a user. Most often, clients are applications and services that want to use Keycloak to secure themselves and provide a single sign-on solution. Clients can also be entities that just want to request identity information or an access token so that they can securely invoke other services on the network that are secured by Keycloak.
- [`group`](https://www.keycloak.org/docs/latest/server_admin/#core-concepts-and-terms)
- [`resource`](https://www.keycloak.org/docs/latest/authorization_services/#resource)
- [`policy`](https://www.keycloak.org/docs/latest/authorization_services/#policy)
- [`scope`](https://www.keycloak.org/docs/latest/authorization_services/#scope)
- [`permissions`](https://www.keycloak.org/docs/latest/authorization_services/#permission)
- `role` vs `group`

## Scratch

> In order to grant/deny access to a `resource`, you need to:
>
> - Define your [policies](https://www.keycloak.org/docs/latest/authorization_services/index.html#_policy_overview)
> - Define your [permissions](https://www.keycloak.org/docs/latest/authorization_services/index.html#_permission_overview)
> - Apply your policies to your permissions
> - Associate your permissions to a `scope` or `resource` (or both)

## Keycloak

### What We Did

1. Spin up service
2. Create a client
   - Client authentication: on
   - Authorization: on
3. Create client scopes:
   - `stac:read`
   - `stac:create`
   - `stac:update`
   - `stac:delete`
4. Create roles
   - `stac-admin` with all `stac:*` scopes
   - `stac-reader` with `stac:read`

RBAC - https://www.keycloak.org/docs/latest/authorization_services/index.html#_policy_rbac

### Things To Learn

What's the difference between a Role and a Group?

> In the IT world the concepts of Group and Role are often blurred and interchangeable. In Keycloak, Groups are just a collection of users that you can apply roles and attributes to in one place. Roles define a type of user and applications assign permission and access control to roles
>
> Aren’t Composite Roles also similar to Groups? Logically they provide the same exact functionality, but the difference is conceptual. Composite roles should be used to apply the permission model to your set of services and applications. Groups should focus on collections of users and their roles in your organization. Use groups to manage users. Use composite roles to manage applications and services.

[source](https://wjw465150.gitbooks.io/keycloak-documentation/content/server_admin/topics/groups/groups-vs-roles.html)

#### Client Registration

##### Initial Access Token

#### Clients

##### Scope Mappers
