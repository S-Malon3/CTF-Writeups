_We just opened a new museum and need your help with finding the flag..._

A WEB challenge presenting a small online gallery. Each piece is viewed at `{url}/n`, and the goal (as always) is to get the server to hand back the flag.

## Recon

The gallery has 7 pieces, each rendered at its own numeric URL (`/1` through `/7`), showing a title, description, artist, medium, and an image. My first instinct was **Path Traversal** directly on that URL parameter, but requesting an out-of-range index (`/99`, `/-1`, etc.) wasn't blocked or redirected, it just rendered a plain "Gallery piece not found" message. That ruled out the simplest form of the idea, but the wording ("not found", rather than a generic error) suggested the ID really was being used to look something up rather than being validated against a fixed range.

The challenge also shipped a `.zip` of the server source. The route handler was doing this:

```js
const stmt = db.prepare(`SELECT * FROM gallery_pieces WHERE id = ${id}`);
```

`id` is `req.params.id` from the URL, spliced straight into the query string with no parameterisation or sanitisation: classic **SQL Injection**.

## Confirming the Injection

Requesting:
```
/1 AND 1=1
```
returned the same piece as `/1`, confirming the value was being evaluated as SQL rather than treated as an opaque ID.

## Building the UNION

Since the row is rendered directly into the page (image, title, description, etc.), a `UNION SELECT` lets us inject an entirely fabricated row of our own choosing, matching the table's 7 columns (`id, title, artist, medium, exhibition_period, description, filename`):

```
/1 AND 1=1 UNION SELECT 1,'a','a','a','a','a','a'
```

This rendered piece `1` with the rest of the row replaced by our dummy `'a'` values, confirming the server was happy to hand back a row we fully controlled. The last column, `filename`, is the interesting one: the server does:

```js
const image = await fs.readFile(path.join(__dirname, 'images', row.filename));
```

with no check that `row.filename` actually stays inside the `images` directory. So whatever we put in that final UNION column gets read straight off disk.

To validate this theory, using an ID far outside the seeded range (so there's no real matching row) and pointing the fake `filename` at an image that does exist on disk:
```
/67 UNION SELECT 1,'a','a','a','a','a','1.webp'
```
This worked, rendering piece `1`'s image despite querying for id `67`. Pointing it at something that doesn't exist instead:
```
/67 UNION SELECT 1,'a','a','a','a','a','h4ck'
```
threw a server error (the `fs.readFile` call fails and falls into the route's catch block, returning a 500). That gave a reliable oracle: valid file path back on disk = a rendered image, invalid = server error. Time to turn that file read into something more interesting than a gallery photo.

## Escaping the Images Directory

The flag is set as an environment variable in the Dockerfile, so it should be readable (as the container's own process) from `/proc/self/environ`. That means using the `filename` column for **Path Traversal** out of the `images/` directory and up to the filesystem root.

A plain `../../` sequence in the URL doesn't survive the trip: Express routes `/:id` as a single path segment, splitting the URL on literal `/` characters *before* decoding anything, so a raw `/` in the payload just gets treated as the start of a new route segment and the request never reaches the handler as one `id` value. This is the same underlying idea behind the Reverse Proxy path-normalisation trick from [Sk8Dog 2025: Reverse Pawxy](../../skateboarding-dog-ctf-2025/reverse-pawxy), a challenge I didn't solve at the time, but learned this lesson from afterwards and was glad to finally put to use here: percent-encoding the slash as `%2F` keeps it inside the single `:id` token during route matching, since Express only URL-decodes each captured segment *after* the route has already matched. By that point the slash reappears intact, ready to be spliced into the SQL query and, from there, straight into the filesystem path.

From there it was trial and error on how many `../` were needed to clear `/app/images` and reach the filesystem root, eventually settling on:

```
../../../../../../proc/self/environ
```

Encoded and dropped into the `filename` column of the UNION payload, the final request became:

```
https://web-museum-xxxxxxxxxxxx.c.sk8.dog/67%20UNION%20SELECT%201,'a','a','a','a','a','..%2F..%2F..%2F..%2F..%2F..%2Fproc%2Fself%2Fenviron'
```

## Reading the Result

The page rendered, but as a blank/broken image: `/proc/self/environ` doesn't have a recognised file extension, so the server's MIME lookup falls back to `application/octet-stream`, which the browser's `<img>` tag can't display. But the raw bytes are still sitting right there, base64-encoded, in the tag's `src` attribute (the app always base64-encodes whatever file it reads and drops it straight into `data:<mimetype>;base64,<data>`). Pulling it back out in the browser console:

```js
atob(document.querySelector('img').src.split(',')[1])
```

decodes the `src` attribute's base64 payload back into the raw contents of `/proc/self/environ`, which includes every environment variable the container was started with, including the `FLAG` variable set in the Dockerfile.

## Lessons Learned
- Route parameters that get treated as "just a number" should never be assumed safe just because the surrounding UI doesn't error strangely. Always check what actually happens to that value server-side (source review beat blind fuzzing here).
- Percent-encoding a `/` to smuggle it past a segment-based router (Express route matching, reverse proxy path normalisation, etc.) is a recurring trick. The common thread is a parser that splits/validates on the *literal, still-encoded* character, then decodes afterwards, letting the "real" character reappear after the check has already passed. Worth actively trying this any time a raw `/` in a payload gets rejected or mis-routed.
- `fs.readFile(path.join(base, userControlled))` is not safe just because `userControlled` didn't come directly from the URL. It still needs to be resolved and checked against the intended base directory (e.g. via `path.resolve` + a prefix check) regardless of how indirectly the attacker got to control it.
- Data rendered into a page isn't limited to what the UI intends to show. A broken/blank `<img>` is still worth pulling apart in devtools, since the data may well still be sitting right there in the DOM.
