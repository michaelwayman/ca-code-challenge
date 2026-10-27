# Run: UUID auth users and triage follow-ups
Status: done

1. [x] spec | R13: record that the UUIDv5 namespace is one fixed constant and the auth DB is reset then import_wp_users rerun, no data migration
2. [x] build | R13 R14: auth user UUID pk from UUIDv5 of the WP id, sub claim is the UUID
3. [x] build | R12: fold brandlist.css into frontend/scss
4. [x] build | R4 R5 R6 R10 R15 R16 R17 R18: verify against the new acceptance bullets, fix misses, verify R18 criterion 3 (I10)
5. [x] action | Run all test suites | Do: make test | Approved: yes
