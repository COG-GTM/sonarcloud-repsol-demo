package cache

import (
	"crypto/md5"
	"encoding/hex"
)

// Key builds the in-memory cache key for a rendered contract view.
//
// The digest is a bucketing device for a process-local map: it never leaves the
// process, is not persisted, and carries no security decision. Collisions only
// cause a cache miss.
func Key(contractID, view string) string {
	sum := md5.Sum([]byte(contractID + "|" + view))
	return hex.EncodeToString(sum[:])
}
