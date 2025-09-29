_"I cant hear it, I think it's breaking up"_

## Initial Analysis
This was a Reverse-Engineering challenge.  The description hinted at a time based element.  The provided binary had to be analyzed to recover the flag, but my Assembly knowledge is limited, so I needed a tool to do the heavy lifting.

## Solve
I bypassed a deep assembly analysis by using an [AI Powered Assembly to C Converter](https://www.codeconvert.ai/assembly-to-c-converter).  The converted code wasn't flawless though.  It needed some manual fixes to run, but it was good enough to reveal the programs core logic.

The key discovery was that the code was printing each character in an unorthodox way to obfuscate the flag, and at an agonisingly slow rate by using `sleep(3600)` to print one character per hour, the event would finish before the flag was printed.  But solving this was easy, I just had to replace the delay with `sleep(0)` and the flag printed immediately.
