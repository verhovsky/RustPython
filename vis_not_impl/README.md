## How to run this

``` sh
cd RustPython
./whats_left.sh | tail -n 1 > vis_not_impl/left.json
cd vis_not_impl
python3 find_imports.py > data1.json

python3 -m http.server
```

Then open http://0.0.0.0:8000/ in a browser.

This assumes the CPython repo is in the same directory as the RustPython repo.
If it's not, modify the `CPYTHON_LIB` variable in `find_imports.py`.
