# Borealis Canonical JSON v1 (CJ)

**Status:** fixed. A structural change would need a new identifier.

The keywords MUST, MUST NOT and SHOULD are used as in RFC 2119.

CJ is the byte-exact serialisation used for **every digest and fingerprint** in Borealis standards and agents. It is a restricted format **inspired by RFC 8785 (JSON Canonicalization Scheme), but not identical to it**: CJ normalises strings to Unicode NFC, and JCS does not. Do not substitute a JCS library.

**The test vectors in [`test-vectors-v1.json`](test-vectors-v1.json) (`canonical_json`) are the authoritative specification.** An implementation is correct only if it reproduces every vector byte for byte.

## Permitted values

| JSON type | Rule |
|---|---|
| object | Keys MUST be ASCII strings and unique |
| array | Any permitted values |
| string | Any Unicode text. It is NFC-normalised before serialisation |
| integer | Range −(2^53−1) to 2^53−1 inclusive |
| `true`, `false`, `null` | As-is |

Floats (any number with a fraction or exponent), NaN and Infinity are **not permitted**. A value containing them cannot be canonicalised, and the operation MUST fail.

## Serialisation
1. NFC-normalise every string value. Keys are ASCII, so normalisation never changes them.
2. Sort object keys ascending by Unicode code point. ASCII-only keys make this the same as byte order.
3. Emit no whitespace. Separators are `,` and `:`.
4. Write integers in shortest decimal form, with `-` for negatives and no leading zeros.
5. Escape strings exactly as follows:
   - `"` → `\"` and `\` → `\\`;
   - U+0008 → `\b`, U+000C → `\f`, U+000A → `\n`, U+000D → `\r`, U+0009 → `\t`;
   - every other code point U+0000–U+001F → `\u00XX` with **lowercase** hex;
   - **no other character is escaped**, including U+007F, non-ASCII characters and U+2028/U+2029. They're written as UTF-8.
6. Encode as UTF-8, with no byte order mark and no trailing newline.

In Python this is exactly:
```python
json.dumps(nfc_normalised(value), ensure_ascii=False, sort_keys=True,
           separators=(",", ":"), allow_nan=False).encode("utf-8")
```
plus the type and range checks above.

## Strict JSON parsing (required of every consumer)
Consumers of Borealis reports MUST reject input that:
- is not valid UTF-8, or starts with a byte order mark;
- contains anything other than exactly one JSON value (trailing data is not permitted);
- has duplicate keys in any object;
- contains `NaN`, `Infinity` or `-Infinity`;
- contains a number with a fraction or exponent, or an integer outside ±(2^53−1).

Producers MUST NOT emit any of these. See the `strict_parsing` test vectors.

## Digests
Wherever a standard says `hex(sha256(CJ(x)))`, it means the lowercase hexadecimal SHA-256 of the CJ bytes of `x`.
