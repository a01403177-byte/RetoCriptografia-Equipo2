CREATE TABLE roles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    auth_sub VARCHAR(255) UNIQUE NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    user_type ENUM('internal', 'external') NOT NULL,
    role_id BIGINT NOT NULL,
    status ENUM('pending', 'active', 'revoked', 'expired') NOT NULL DEFAULT 'pending',
    end_date DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_role FOREIGN KEY (role_id) REFERENCES roles(id)
);

CREATE TABLE permissions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    UNIQUE KEY uniq_permissions_resource_action (resource, action)
);

CREATE TABLE role_permissions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    role_id BIGINT NOT NULL,
    permission_id BIGINT NOT NULL,
    UNIQUE KEY uniq_role_permissions (role_id, permission_id),
    CONSTRAINT fk_role_permissions_role FOREIGN KEY (role_id) REFERENCES roles(id),
    CONSTRAINT fk_role_permissions_permission FOREIGN KEY (permission_id) REFERENCES permissions(id)
);

CREATE TABLE audit_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    event_type VARCHAR(80) NOT NULL,
    actor_user_id BIGINT NULL,
    target_user_id BIGINT NULL,
    action VARCHAR(80) NOT NULL,
    resource VARCHAR(120) NULL,
    result ENUM('success', 'failure') NOT NULL,
    metadata_json JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO roles (code, name) VALUES
    ('ADMIN', 'Administrador'),
    ('HUMANITARIA', 'Humanitaria'),
    ('LEGAL_TI', 'Legal TI'),
    ('LECTURA', 'Solo lectura'),
    ('EXTERNAL', 'Externo');

INSERT INTO permissions (resource, action) VALUES
    ('users', 'create'),
    ('users', 'view'),
    ('users', 'update'),
    ('users', 'activate'),
    ('users', 'revoke'),
    ('users', 'reactivate'),
    ('users', 'change_role'),
    ('audit', 'view'),
    ('records', 'view'),
    ('records', 'edit'),
    ('documents', 'view'),
    ('documents', 'edit');

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p
WHERE
    (r.code = 'ADMIN' AND (p.resource, p.action) IN (
        ('users', 'create'),
        ('users', 'view'),
        ('users', 'update'),
        ('users', 'activate'),
        ('users', 'revoke'),
        ('users', 'reactivate'),
        ('users', 'change_role'),
        ('audit', 'view')
    ))
    OR (r.code = 'HUMANITARIA' AND (p.resource, p.action) IN (
        ('records', 'view'),
        ('records', 'edit')
    ))
    OR (r.code = 'LEGAL_TI' AND (p.resource, p.action) IN (
        ('documents', 'view'),
        ('documents', 'edit')
    ))
    OR (r.code = 'LECTURA' AND (p.resource, p.action) IN (
        ('records', 'view'),
        ('documents', 'view')
    ))
    OR (r.code = 'EXTERNAL' AND (p.resource, p.action) IN (
        ('documents', 'view')
    ));
