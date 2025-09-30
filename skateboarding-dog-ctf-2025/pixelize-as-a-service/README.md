## Initial Analysis
The "Pixelize as a Service" challenge was part of of the Skateboarding Dog CTF 2025 game that involved a dog which could pixelise images at 1x, 2x and 4x scale,  My first interaction with it was actually while solving the Touch Grass challenge, where I thought uploading a specific image to the PaaS booth was a required Step.

When I uploaded the previous flag image, it returned a completely transparent image instead of a pixelated one.  This seemed suspicious, and therefore I thought it was a lead.

I spent a significant amount of time analyzing this transparent output for hidden data, such as:
 - File Metadata
 - Steganography using tools like steghide and binwalk
 - Data hidden in RGBA channels
 - Comparing differences between different scales

Despite my efforts, this investigation turned up nothing.  In hindsight, I believe this was the wrong approach, but I gave up here to shift focus on other challenges.
