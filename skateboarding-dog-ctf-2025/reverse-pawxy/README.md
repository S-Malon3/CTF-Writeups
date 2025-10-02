
A web challenge involving a reverse proxy that allows health checks on a backend API without exposing the servers secrets (the flag!)

## Recon
Initial active scanning with **OWASP ZAP** revealed the servers response headers disclosed:
- **Server OS Information:** Nginx/1.18.0

I attempted to find known exploits for this Nginx version via **ExploitDB**, but no relevant results were found.

### HTTP Method Fuzzing
Using **OWASP ZAP**, I fuzzed various HTTP Methods:
 - **GET:** Standard 200 OK response
 - **POST, PUT, DELETE, etc:** Returns 405 "Method Not Allowed"
 - **TRACE:** Returns 405 "Not Allowed"
I found the fact that **TRACE** was returning 405 with a different message fascinating, and on top of this, it returned HTML despite `accept: text/json`, with an interesting HTML comment:
```HTML
<!-- a padding to disable MSIE and Chrome friendly error page -->
<!-- a padding to disable MSIE and Chrome friendly error page -->
<!-- a padding to disable MSIE and Chrome friendly error page -->
<!-- a padding to disable MSIE and Chrome friendly error page -->
<!-- a padding to disable MSIE and Chrome friendly error page -->
<!-- a padding to disable MSIE and Chrome friendly error page -->
```
This indicated disabling of MSIE and Chrome's friendly error pages. browser specific error handling, and I put in different user agents in the headers (including none) to see if I got any different responses, however nothing interesting stood out despite those comments being absent in some browsers.

### Directory Mapping
Ran **GoBuster** which discovered only
```
/
/index.html
/healthcheck (the API server)
```
So no hidden directories.

## Exploit
The difference in the TRACE requests response hinted at different HTTP Parsers in the chain, it's likely that **POST, PUT, etc** we're configured to be blocked by the Reverse Proxy, but **TRACE** was being handled by the end server.  This sounded like a HTTP Request Smuggling exploit, based off this I attempted CL.TE _(Content-Length vs Transfer-Encoding)_ Smuggling

```HTTP
POST /healthcheck HTTP/1.1
Host: sk8.dog
Content-Length: 6
Transfer-Encoding: chunked

0

GET /healthcheck HTTP/1.1
Host: sk8.dog
```
**In Theory:** The proxy might honor `Transfer-Encoding: chunked` and see the request ending after 0, while the back end might honor `Content-Length: 6` and treat the second GET request as a second request.

I was not able to find a payload which worked, I also attempted TE:CL _(Transfer Encoding vs Content Length)_ but also to no success.

## The missing piece
The solution to this challenge ended up revolving around Path Traversal using a Path Normalisation bypass

### The Attack Breakdown
```bash
curl --path-as-is -i -s -k 'https://web-reverse-pawxy-3b34be52c2cc.c.sk8.dog/healthcheck%2fH4CK/../flag'
```
1. `--path-as-is` Prevents curl from normalising the path before sending.
2. `-i` include HTTP Response headers in output
3. `-s` hide progress bar, curl status messages, etc
4. `-k` allow connection to SSL without certificate verification
5. `%2fH4CK`:
    1. `%2f` URL-encoded forward slash (`/`)
    2. `H4CK` Dummy directory name, this does not matter, but without `%2fH4CK` the path `/healthcheck/..` gets turned to to `/healthcheck/..` which just returns to `index.html`.  With `healthcheck%2fH4CK/..` the path becomes `healthcheck/H4CK/..` which returns to the end servers root, and doing `healthcheck/H4ck/..` directly returns nothing, so there is a security mechanism in place preventing this which using encoded characters bypasses.
6. `/flag` go to the flags directory, this successfully returns the flag.

### Why I Missed This
When I ran GoBuster, I ran it on `c.sk8.dog/` not `c.sk8.dog/healthcheck` therefore every directory I checked was being run from the web servers root, not against the API server through the Reverse Proxy, and therefore my GoBuster scan never interacted with the API Server beyond `/healthcheck.  With that in mind, the solution method of Path Traversal was too complex for GoBuster, but when GoBuster returned nothing I thought of this as a dead end.

## Lessons Learned
- I did not know about the concept of Path Normalisation until this challenge, and the use of ``--path-as-is`` and encoded characters (`%2f`, `%5c`) are an effective tool for me to use going forwards.
- GoBuster only shows hidden directories, not more advanced methods of Path Traversal, and I should not rule out an attack vector based off a single tools results.
