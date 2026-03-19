#!/bin/sh
set -e

# Ensure we are in ygg repo
cd /home/ian/ygg

# 1. Launch a scout raven
FLIGHT_PURPOSE="Initial RAVENS command cycle test"
OUTPUT=$(./commands/raven/launch --trigger "test-init" "$FLIGHT_PURPOSE")
echo "Launch output: $OUTPUT"

# Extract flight ID from output (it prints "Flight launched: RAVEN-...")
FLIGHT_ID=$(echo "$OUTPUT" | grep -o 'RAVEN-[^ ]*' | head -n1)
echo "Flight ID: $FLIGHT_ID"

# Validate found
if [ -z "$FLIGHT_ID" ]; then echo "Failed to parse flight ID"; exit 1; fi

# 2. Simulate evidence gathering
EVIDENCE_DIR=state/runtime/ravens/tests
mkdir -p "$EVIDENCE_DIR"
echo "Test evidence" > "$EVIDENCE_DIR/evidence.txt"
EVIDENCE_REF="file://$(pwd)/state/runtime/ravens/tests/evidence.txt"

# 3. Return the flight (Muninn processing)
./commands/raven/return "$FLIGHT_ID" --evidence "$EVIDENCE_REF" --failure-condition "None observed" --recommendation "Test RAVENS cycle run" --adjudication ADOPT --promotion LOG_DAILY
echo "Return processed."

# 4. Adjudicate (spine decision)
./commands/spine/adjudicate/adjudicate "$FLIGHT_ID" "ADOPT"
echo "Adjudicated as ADOPT."

# 5. Show latest log entries
echo "=> Latest Raven logs:"
tail -n 10 state/runtime/ravens/logs/ravens.jsonl