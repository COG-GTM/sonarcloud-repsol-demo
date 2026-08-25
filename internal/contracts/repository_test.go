package contracts_test

import (
	"testing"

	"github.com/cognition/sonar-remediation-demo/internal/contracts"
	"github.com/cognition/sonar-remediation-demo/internal/store"
)

func TestFindByCustomerReturnsMatches(t *testing.T) {
	db, err := store.Open()
	if err != nil {
		t.Fatalf("open store: %v", err)
	}
	defer db.Close()

	rows, err := contracts.FindByCustomer(db, "Iberdrola")
	if err != nil {
		t.Fatalf("find: %v", err)
	}
	if len(rows) != 1 || rows[0].ID != "C-1001" {
		t.Fatalf("expected only C-1001, got %+v", rows)
	}
}

func TestCountByValidatedRegion(t *testing.T) {
	db, err := store.Open()
	if err != nil {
		t.Fatalf("open store: %v", err)
	}
	defer db.Close()

	n, err := contracts.CountByValidatedRegion(db, "ES-01")
	if err != nil {
		t.Fatalf("count: %v", err)
	}
	if n != 2 {
		t.Fatalf("expected 2 contracts in ES-01, got %d", n)
	}
}
