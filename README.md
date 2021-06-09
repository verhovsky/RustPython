<img src="./logo.png" width="125" height="125" align="right" />

# [RustPython](https://rustpython.github.io/)

A Python 3 (CPython >= 3.8) interpreter written in Rust :snake: :scream:
:metal:.

[![Build Status](https://github.com/RustPython/RustPython/workflows/CI/badge.svg)](https://github.com/RustPython/RustPython/actions?query=workflow%3ACI)
[![codecov](https://codecov.io/gh/RustPython/RustPython/branch/master/graph/badge.svg)](https://codecov.io/gh/RustPython/RustPython)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Contributors](https://img.shields.io/github/contributors/RustPython/RustPython.svg)](https://github.com/RustPython/RustPython/graphs/contributors)
[![Gitter](https://badges.gitter.im/RustPython/Lobby.svg)](https://gitter.im/rustpython/Lobby)
[![docs.rs](https://docs.rs/rustpython/badge.svg)](https://docs.rs/rustpython/)
[![Crates.io](https://img.shields.io/crates/v/rustpython)](https://crates.io/crates/rustpython)
[![dependency status](https://deps.rs/crate/rustpython/0.1.1/status.svg)](https://deps.rs/crate/rustpython/0.1.1)
[![WAPM package](https://wapm.io/package/rustpython/badge.svg?style=flat)](https://wapm.io/package/rustpython)
[![Open in Gitpod](https://img.shields.io/static/v1?label=Open%20in&message=Gitpod&color=1aa6e4&logo=gitpod)](https://gitpod.io#https://github.com/RustPython/RustPython)

## Usage

#### Check out our [online demo](https://rustpython.github.io/demo/) running on WebAssembly.

RustPython requires the latest stable version of Rust (i.e. 1.53 as of June 17, 2021).
You can check your Rust version with `rustc --version` and run `rustup update stable` if you need to update.

To build RustPython locally, do the following:

    $ git clone https://github.com/RustPython/RustPython
    $ cd RustPython
    $ cargo run --release demo.py
    Hello, RustPython!

(`--release` is needed (at least on Windows) to prevent stack overflow)

Or use the interactive shell:

    $ cargo run --release
    Welcome to the magnificent RustPython interpreter
    >>>>> 2+2
    4

You can also install and run RustPython with `cargo`:

    $ cargo install --git https://github.com/RustPython/RustPython
    $ rustpython
    Welcome to the magnificent RustPython interpreter
    >>>>>

(The `rustpython-*` crates have been yanked from https://crates.io/ due to being out
of date and not building on newer Rust versions; we hope to release a new
version Soon™)

If you'd like to make HTTPS requests, you can enable the `ssl` feature, which
also lets you install the `pip` package manager. Note that on Windows, you may
need to install OpenSSL, or you can enable the `ssl-vendor` feature instead,
which compiles OpenSSL for you but requires a C compiler, Perl, and `make`.

Once you've installed RustPython with SSL support, you can install pip by
running:

    $ rustpython --install-pip

You can also install RustPython through the `conda` package manager, though
this isn't officially supported and may be out of date:

    $ conda install rustpython -c conda-forge
    $ rustpython


### WASI

You can compile RustPython to a standalone WebAssembly WASI module so it can run anywhere.

```shell
$ wapm install rustpython
$ wapm run rustpython
>>>>> 2+2
4
```

#### Building the WASI file

You can build the WebAssembly WASI file with:

```
cargo build --release --target wasm32-wasi --features="freeze-stdlib"
```

> Note: we use `freeze-stdlib` to include the standard library inside the binary.

### JIT compiler

RustPython has a **very** experimental just-in-time (JIT) compiler that compiles Python functions into native code.

#### Building

By default the JIT compiler isn't enabled, it's enabled with the `jit` cargo feature.

    $ cargo run --features jit
    
This requires autoconf, automake, libtool, and clang to be installed.

#### Using 

To compile a function, call `__jit__()` on it.

```python
def foo():
    a = 5
    return 10 + a

foo.__jit__()  # this will compile foo to native code and subsequent calls will execute that native code
assert foo() == 15
```

## Embedding RustPython into your Rust Applications

Interested in exposing Python scripting in an application written in Rust,
perhaps to allow quickly tweaking logic where Rust's compile times would be inhibitive?
Then `examples/hello_embed.rs` and `examples/mini_repl.rs` may be of some assistance.

## Disclaimer

RustPython is in development, and while the interpreter certainly can be used
in interesting use cases like running Python in WASM and embedding into a Rust
project, do note that RustPython is not totally production-ready.

Contribution is more than welcome! See our contribution section for more
information on this.

## Conference videos

Check out these conference talks:

- [FOSDEM 2019](https://www.youtube.com/watch?v=nJDY9ASuiLc)
- [EuroPython 2018](https://www.youtube.com/watch?v=YMmio0JHy_Y)

## Use cases

Although RustPython is a fairly young project, a few people have used it to
make cool projects:

- [pyckitup](https://github.com/pickitup247/pyckitup): a game engine written in
  Rust.
- [Robot Rumble](https://github.com/robot-rumble/logic/): an arena-based AI competition platform

## Goals

- Full Python 3 environment entirely in Rust (not CPython bindings)
- A clean implementation without compatibility hacks

## Documentation

Currently along with other areas of the project, documentation is still in an
early phase.

You can read the [online documentation](https://docs.rs/rustpython-vm) for the
latest release, or the [user guide](https://rustpython.github.io/docs/).

You can also generate documentation locally by running:

```shell
$ cargo doc # Including documentation for all dependencies
$ cargo doc --no-deps --all # Excluding all dependencies
```

Documentation HTML files can then be found in the `target/doc` directory.

## Contributing

Contributions are more than welcome, and in many cases we are happy to guide
contributors through PRs or on [Gitter](gitter). Please refer to the
[development guide](DEVELOPMENT.md) as well.

With that in mind, please note that this project is maintained by volunteers, some of
the best ways to get started are below:

Most tasks are listed in the
[issue tracker](https://github.com/RustPython/RustPython/issues). Check issues
labeled with `good first issue` if you wish to start coding.

To enhance CPython compatibility, try to increase unit test coverage by checking this article: [How to contribute to RustPython using CPython's unit tests](https://rustpython.github.io/guideline/2020/04/04/how-to-contribute-by-cpython-unittest.html)

Another approach is to checkout the source code: builtin functions and object
methods are often the simplest and easiest way to contribute.

You can also simply run `./whats_left.sh` to assist in finding any unimplemented
method.

## Compiling to WebAssembly

[See this doc](wasm/README.md)

## Community

Chat with us on [Gitter][gitter].

## Code of conduct

Our code of conduct [can be found here](code-of-conduct.md).

## Credit

The initial work was based on
[windelbouwman/rspython](https://github.com/windelbouwman/rspython) and
[shinglyu/RustPython](https://github.com/shinglyu/RustPython)

[gitter]: https://gitter.im/rustpython/Lobby

## Links

These are some useful links to related projects:

- https://github.com/ProgVal/pythonvm-rust
- https://github.com/shinglyu/RustPython
- https://github.com/windelbouwman/rspython

## License

This project is licensed under the MIT license. Please see the
[LICENSE](LICENSE) file for more details.

The [project logo](logo.png) is licensed under the CC-BY-4.0
license. Please see the [LICENSE-logo](LICENSE-logo) file
for more details.
