_securing file uploads is easy when you have a rich standard library!_

A WEB challenge involving a Flask server that hands out the flag on a successful file upload, provided the uploaded file passes three checks.

**Note:** I did not finish this one myself. I got partway through before running out of time, and a teammate finished it off (on my session/access) while I wasn't at the keyboard. This writeup covers what I tried, and then the actual solve, worked out from the server source and the commands my teammate ran.

## The Challenge

The upload endpoint (`guesstype.py`) runs three checks against the uploaded file before returning the flag:

1. A file was actually sent.
2. The filename's extension (via `pathlib.Path(filename).suffix`) must equal `.dog`.
3. Python's `mimetypes.guess_type(filename)` must decide the filename's guessed MIME type is `skateboarding/dog`.

The key thing I didn't clock at the time: **none of these checks touch the file's contents, only the client-supplied `filename` string.** There is no magic-byte sniffing, no `Content-Type` header check: `mimetypes.guess_type()` in Python works purely off the filename you hand it.

## What I Tried

My first attempt was a blank text file literally named `skateboarding.dog`. This passed checks 1 and 2 but failed check 3: `mimetypes.guess_type("skateboarding.dog")` returns nothing useful on a stock Python install, since `.dog` isn't a registered extension anywhere.

My next assumption was that this was a content-sniffing problem, so I reached for **Burp Suite** and tried tampering with the `Content-Type` header on the multipart part (setting it to `skateboarding/dog` directly), assuming the server was inspecting that. It didn't work, which in hindsight makes total sense: the route never reads `user_file.content_type` or the file bytes at all, only `user_file.filename`. What I did notice was that Burp let me freely rewrite whatever I wanted in the replayed request and the server happily processed it without complaint, which was the correct instinct (the filename is 100% attacker-controlled). I just hadn't landed on manipulating the *filename string itself* into something `mimetypes.guess_type()` would misparse before I had to step away.

## The Actual Solve

The bug is in `mimetypes.guess_type()` itself. Since Python 3.11, this function special-cases strings that look like `data:` URIs (RFC 2397 data URLs): if the input starts with `data:`, it parses the media type straight out of the string (`data:<mediatype>,<data>`) instead of doing extension lookup at all.

Meanwhile, `pathlib.Path(filename).suffix` only ever looks at the last `/`-separated path segment, and takes the extension from *that*.

So a filename can be crafted where those two functions read completely different parts of the same string. My teammate's filename was:

```
data:skateboarding/dog,x.dog
```

- **`Path(...).suffix`**: pathlib splits on `/`, giving path segments `data:skateboarding` and `dog,x.dog`. The suffix of the final segment `dog,x.dog` is `.dog` → **check 2 passes.**
- **`mimetypes.guess_type(...)`**: sees the string starts with `data:`, parses it as a data URL, and extracts the media type as everything between `data:` and the first `,` → `skateboarding/dog` → **check 3 passes.**

I confirmed this behaviour locally in a Python REPL: `Path(fn).suffix` and `mimetypes.guess_type(fn)` really do disagree on which part of the string they're parsing, and exactly the way described above.

The first attempt at delivering this was via `curl`, setting the filename on the multipart field directly:
```bash
curl -X POST https://web-guesstype-xxxxxxxxxxxx.c.sk8.dog/upload \
  -F 'file=@/etc/hostname;filename=data:skateboarding/dog,x.dog'
```
This failed: curl's `-F` parser treats the field value as a semicolon-separated list of `key=value` pairs, so `filename=data:skateboarding/dog,x.dog` gets mangled by the `:` and `/` in the value, and curl throws `Failed to open/read local data from file/application` trying to interpret part of it as another directive.

Switching to Python's `requests` library sidesteps that entirely, since the filename can be passed as a plain string in a tuple and gets dropped straight into the multipart body without any of curl's field-syntax parsing getting in the way. See [`SOLVE.py`](./SOLVE.py) for the exact script used: it posts a dummy one-byte file with that crafted filename and gets a `200` with the flag back in the JSON response.

## Lessons Learned
- `mimetypes.guess_type()` is not a file-type validator: it is a filename/URL heuristic, and since Python 3.11 it explicitly understands `data:` URI syntax. Passing untrusted, attacker-controlled strings into it is dangerous if the result gates any kind of trust decision.
- `pathlib.Path.suffix` and `mimetypes.guess_type()` do not necessarily agree on what "the extension" of a string is. `Path.suffix` only looks at the final `/`-delimited segment, while `guess_type()` can bypass extension logic altogether for `data:` strings. Chaining two different parsers as two "independent" checks on the same untrusted input is not actually independent if the parsers disagree on structure.
- When a check clearly isn't reacting to file *content* (headers, magic bytes, `Content-Type`) no matter what's tampered with in Burp, stop and re-read the server code for what value is actually being validated. Here it was the `filename` string the whole time, not the file itself.
