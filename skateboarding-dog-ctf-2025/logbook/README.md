This CTF revolved around a basic logging page for users to log messages.

## Recon
The logging page displayed the contents of the message on the page, so my first attempt was DOM Injection with Javascript to inser `<script>alert(1)</script>`, which didnt work, so I used a more advanced method
```html
<img src=x onerror=alert(1)>
```
This successfully gave an alert, so I knew I had an attack vector.

Next, while testing I saw an error in the console
`TypeError: can't access property "then", a.default.detectStore(...) is undefined`.  The code throwing this error is public, and after asking AI to analyse it _(lol)_ it seems to be related to Shopify.  The solution likely lies in overwriting `a.default.detectStore()` to insert my own Malicious code.

## Exploitation
### Crafting the Initial Payload
I came up with another source to inject code.
```html
<body onload="alert(1)"></body>
```
because that allowed me to add code to the load of the page, hopefully before the `detectStore` code was running.  I crafted a payload:
```js
// definition payload
if (typeof a === "undefined") {
    a = {
        default: {
            detectStore: function() {
                return Promise.resolve({
                    id: "1337",
                    name: "hacked-store",
                    adblockState: {
                        mayNeedWhitelist: false
                    },
                    metadata: {
                        tagInSameTab: true,
                        flag: "test"
                    }
                });
            }
        }
    };
}
```
and also another payload to tell me if `a.default.detectStore` exists in the scope that the code is being injected into.
```js
//alert payload
setTimeout(() => {
    alert("a exists: " + (typeof a !== "undefined"))
}, 1000)
```
Currently, when I have both these injected on layout, I get redirected to a page saying **"No hacking pls"**, but only if both of these payloads have been injected.  If either one are defined individually, I get no error.  This tells me that if I attempt to access `a.default.detectStore()` with my own code while it's actually defined, i'll set off some sort of "alarm", since the alert payload doesn't trip the alarm until my definition payload is injected, that implies that `a.default.detectStore()` is successfully being defined.  However, I still get an error when refreshing the page that it doesn't exist.

## Winning the Race
Since I belive i'm defining `a.default.detectStore` properly, what's left for me to do is make it defined before the Shopify script which is still failing due to it not being defined.

Looking back at the Shopify Code, I noticed it's an IIFE _(Immediately Involed Function Execution)_, which seems to be running on page load (before the logs are loaded).  So no matter what I do, I can't make my payloads in the logs execute before the Shopify code.  I tried subverting this by using `$(document).ready()` but to no success.  At this point I shifted focus to other challenges hoping I would come to a sudden realisation, but it never came.
