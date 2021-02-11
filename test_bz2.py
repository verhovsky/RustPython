import bz2


c = bz2.BZ2Compressor()
inp = b"I hope it works!"
print("inp", inp)

out = c.compress(inp)
out += c.flush()
print("out", out)

d = bz2.BZ2Decompressor()
results = []
for i in range(15):
    print(i)
    resp = d.decompress(out if i == 0 else b"")
    results.append(resp)
    print("got", resp)
    if d.eof:
        print("eof yes")
        break
    else:
        print("eof: no")
    print()

    raise

back_to_inp = b"".join(results)
print(
    "res",
)

assert inp == back_to_inp

# a = bz2.BZ2Compressor()
# b = []
# c = a.compress(b"hello" * 100000)
# b.append(c)
# print(c)
# c = a.compress(b"hello" * 100000)
# b.append(c)
# print(c)
# c = a.flush()
# b.append(c)
# print(c)

# test errors
# print(a.compress(b"hello"))
# print(a.flush())
