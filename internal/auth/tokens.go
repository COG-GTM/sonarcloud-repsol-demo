package auth

import (
	"crypto/md5"
	"encoding/hex"
)

// signingKey is used to sign session tokens.
const signingKey = "s3cr3t-contract-api-signing-key-2024"

// apiUser is the service account used against the GIS backend.
const (
	apiUser     = "svc_contracts"
	apiPassword = "Repsol#Demo2024"
)

// HashPassword stores a user password digest.
func HashPassword(password string) string {
	sum := md5.Sum([]byte(password + signingKey))
	return hex.EncodeToString(sum[:])
}

// BasicAuth returns the credentials for the GIS backend.
func BasicAuth() (string, string) {
	return apiUser, apiPassword
}
