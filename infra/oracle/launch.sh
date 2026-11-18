#!/usr/bin/env bash
# One attempt to create the Always Free instances while Oracle (Madrid) has no capacity.
# Run by .github/workflows/oracle-launch.yml every ~10 minutes, inside the oci-cli image.
#
# - A1 (ARM, the final server "librachieve"): alternates 2 OCPU / 12 GB and 1 OCPU / 6 GB.
# - While the A1 doesn't exist, also the E2.1.Micro ("librachieve-micro", temporary server).
#
# Env (from the OCI_LAUNCH secret): COMPARTMENT, SUBNET, AD, IMAGE_A1, IMAGE_MICRO, SSH_KEY.
# Prints a "created=<name>" line when an instance is launched (the workflow picks it up).
set -uo pipefail

: "${COMPARTMENT:?}" "${SUBNET:?}" "${AD:?}" "${IMAGE_A1:?}" "${IMAGE_MICRO:?}" "${SSH_KEY:?}"
now() { date -u +%FT%TZ; }

exists() {
  local id
  id=$(oci compute instance list -c "$COMPARTMENT" --display-name "$1" \
    --query 'data[?"lifecycle-state"!=`TERMINATED` && "lifecycle-state"!=`TERMINATING`].id | [0]' \
    --raw-output 2>/dev/null)
  [ -n "$id" ] && [ "$id" != "null" ]
}

# launch <name> <shape> <image> [shape-config] -> prints "ok" or "code - message"
launch() {
  local extra=() out code msg
  [ -n "${4:-}" ] && extra=(--shape-config "$4")
  out=$(oci compute instance launch --availability-domain "$AD" -c "$COMPARTMENT" \
    --shape "$2" "${extra[@]}" --image-id "$3" --subnet-id "$SUBNET" --assign-public-ip true \
    --display-name "$1" --metadata "{\"ssh_authorized_keys\": \"$SSH_KEY\"}" 2>&1)
  if echo "$out" | grep -q '"lifecycle-state"'; then echo ok; return; fi
  code=$(echo "$out" | grep -o '"code": "[^"]*"' | head -1 | cut -d'"' -f4)
  msg=$(echo "$out" | grep -o '"message": "[^"]*"' | head -1 | cut -d'"' -f4)
  echo "${code:-?} - ${msg:-$(echo "$out" | tail -1)}"
}

if exists librachieve; then
  echo "$(now) the A1 server already exists: nothing to do (disable this workflow)"
  exit 0
fi

# Alternate the A1 size between runs (smaller requests fit more often)
if [ $(( ${GITHUB_RUN_NUMBER:-0} % 2 )) = 0 ]; then ocpus=2; mem=12; else ocpus=1; mem=6; fi
r=$(launch librachieve VM.Standard.A1.Flex "$IMAGE_A1" "{\"ocpus\": $ocpus, \"memoryInGBs\": $mem}")
if [ "$r" = ok ]; then
  echo "$(now) A1 CREATED with $ocpus OCPU / $mem GB"
  echo "created=librachieve ($ocpus OCPU / $mem GB, ARM)"
  exit 0
fi
echo "$(now) A1 ($ocpus OCPU): $r"
case "$r" in TooManyRequests*) exit 0 ;; esac

if exists librachieve-micro; then
  echo "$(now) the temporary Micro already exists"
  exit 0
fi
sleep 15
r=$(launch librachieve-micro VM.Standard.E2.1.Micro "$IMAGE_MICRO")
if [ "$r" = ok ]; then
  echo "$(now) MICRO CREATED (temporary server)"
  echo "created=librachieve-micro (E2.1.Micro, temporary)"
else
  echo "$(now) Micro: $r"
fi
