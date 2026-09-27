import requests

r = requests.post(
    "https://web-guesstype-93tya0f855m7xd.c.sk8.dog/upload",
    files={"file": ("data:skateboarding/dog,x.dog", b"x")},
)
print(r.status_code, r.text)
