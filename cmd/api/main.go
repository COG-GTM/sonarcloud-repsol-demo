package main

import (
	"log"
	"net/http"
	"os"

	"github.com/cognition/sonar-remediation-demo/internal/store"
	"github.com/cognition/sonar-remediation-demo/internal/web"
)

func main() {
	db, err := store.Open()
	if err != nil {
		log.Fatalf("cannot open demo database: %v", err)
	}
	defer db.Close()

	addr := os.Getenv("ADDR")
	if addr == "" {
		addr = ":8080"
	}

	srv := &web.Server{DB: db}
	log.Printf("contract desk listening on http://localhost%s", addr)
	if err := http.ListenAndServe(addr, srv.Routes()); err != nil {
		log.Fatal(err)
	}
}
