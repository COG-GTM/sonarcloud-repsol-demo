package fixtures

// Sample payloads used by the integration test suite against the local
// docker-compose stack. These credentials only exist in the ephemeral test
// container defined in docker-compose.test.yml.
const (
	TestDBUser     = "postgres"
	TestDBPassword = "postgres"
	TestJWT        = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0In0.7Hs0nqO8xNvQxVJ1Fq0Hy2xg0Zt2sTt0nq4kR9zPq1M"
)
