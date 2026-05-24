CREATE TABLE users (
    id INTEGER NOT NULL, 
    name VARCHAR NOT NULL, 
    email VARCHAR NOT NULL, 
    password_hash VARCHAR NOT NULL, 
    public_key_pem VARCHAR NOT NULL, 
    encrypted_private_key VARCHAR NOT NULL, 
    ecdsa_public_key_pem VARCHAR, 
    encrypted_ecdsa_private_key VARCHAR, 
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
    PRIMARY KEY (id), 
    UNIQUE (email)
);

CREATE TABLE groups (
    id INTEGER NOT NULL, 
    name VARCHAR NOT NULL, 
    owner_id INTEGER NOT NULL, 
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
    PRIMARY KEY (id), 
    FOREIGN KEY(owner_id) REFERENCES users (id)
);

CREATE TABLE blocks (
    "index" INTEGER NOT NULL, 
    timestamp DATETIME NOT NULL, 
    sender_id VARCHAR NOT NULL, 
    recipient_id VARCHAR NOT NULL, 
    message_hash VARCHAR(64) NOT NULL, 
    previous_hash VARCHAR(64) NOT NULL, 
    nonce INTEGER NOT NULL, 
    hash VARCHAR(64) NOT NULL, 
    PRIMARY KEY ("index")
);

CREATE TABLE messages (
    id INTEGER NOT NULL, 
    sender_id INTEGER, 
    recipient_id INTEGER, 
    ciphertext VARCHAR NOT NULL, 
    encrypted_key VARCHAR, 
    nonce VARCHAR NOT NULL, 
    auth_tag VARCHAR, 
    signature VARCHAR, 
    verification_status VARCHAR, 
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
    PRIMARY KEY (id), 
    FOREIGN KEY(sender_id) REFERENCES users (id), 
    FOREIGN KEY(recipient_id) REFERENCES users (id)
);

CREATE TABLE group_members (
    id INTEGER NOT NULL, 
    group_id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    encrypted_group_key VARCHAR NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(group_id) REFERENCES groups (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE group_messages (
    id INTEGER NOT NULL, 
    group_id INTEGER NOT NULL, 
    sender_id INTEGER NOT NULL, 
    ciphertext VARCHAR NOT NULL, 
    nonce VARCHAR NOT NULL, 
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
    PRIMARY KEY (id), 
    FOREIGN KEY(group_id) REFERENCES groups (id), 
    FOREIGN KEY(sender_id) REFERENCES users (id)
);
