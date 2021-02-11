use std::fmt;
use std::io::Write;

use crate::builtins::pytype::PyTypeRef;
use crate::byteslike::PyBytesLike;
use crate::common::lock::PyMutex;
use crate::function::OptionalArg;
use crate::pyobject::{PyClassImpl, PyObjectRef, PyResult, PyValue, StaticType};
use crate::VirtualMachine;
use bzip2::write::BzEncoder;
use bzip2_rs::decoder::{Decoder, ReadState, WriteState};

struct DecompressorState {
    eof: bool,
    needs_input: bool,
    unused_data: Vec<u8>,
    decoder: Decoder,
}

#[pyclass(module = "_bz2", name = "BZ2Decompressor")]
struct BZ2Decompressor {
    state: PyMutex<DecompressorState>,
}

impl fmt::Debug for BZ2Decompressor {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "_bz2.BZ2Compressor")
    }
}

impl PyValue for BZ2Decompressor {
    fn class(_vm: &VirtualMachine) -> &PyTypeRef {
        Self::static_type()
    }
}

#[pyimpl]
impl BZ2Decompressor {
    #[pymethod]
    fn decompress(
        &self,
        data: PyBytesLike,
        // TODO: PyIntRef
        max_length: OptionalArg<i32>,
        vm: &VirtualMachine,
    ) -> PyResult {
        // TODO: make const
        let bufsiz = 8192;
        let max_length = max_length.unwrap_or(-1);
        let max_length = if max_length < 0 || max_length >= bufsiz {
            bufsiz
        } else {
            max_length
        };
        // println!("{}", max_length);

        let mut state = self.state.lock();
        let DecompressorState {
            eof,
            needs_input,
            unused_data,
            decoder,
        } = &mut *state;

        data.with_ref(|data| {
            match decoder.write(&data).unwrap() {
                WriteState::Written(written) => {
                    println!("wrote {} byte(s)", written);
                    Ok(written)
                }
                // TODO
                WriteState::NeedsRead => {
                    return Err(vm.new_runtime_error("couldn't write data".to_owned()))
                }
            }
        });

        // TODO: check that max_length = 0 works correctly
        // TODO
        // let mut buf = Vec::with_capacity(max_length as usize);
        let mut buf = [0; 8192];
        match decoder.read(&mut buf) {
            Ok(ReadState::NeedsWrite(space)) => {
                println!("NeedsWrite {:?}", space);
                *needs_input = true;
            }
            Ok(ReadState::Read(n)) => {
                println!("Read {:?}", n);
                println!("Data {:?}", buf);
                // `n` uncompressed bytes have been read into `buf`
                // TODO: need input?
                *needs_input = false;
                // TODO: ask author to make this public.
                // we need to set eof = true as soon as we reach the end of the file.
                // if decoder.eof {
                //     *eof = true;
                // }
                return Ok(vm.ctx.new_bytes(buf[..n].to_vec()));
            }
            Ok(ReadState::Eof) => {
                println!("EOF");
                *needs_input = false;
                *eof = true;
            }
            // TODO
            _ => return Err(vm.new_runtime_error("couldn't read bz2".to_owned())),
        }
        Ok(vm.ctx.new_bytes(b"".to_vec()))
    }

    #[pyproperty]
    fn eof(&self, vm: &VirtualMachine) -> PyObjectRef {
        let state = self.state.lock();
        vm.ctx.new_bool(state.eof)
    }

    #[pyproperty]
    fn unused_data(&self, vm: &VirtualMachine) -> PyObjectRef {
        // Data found after the end of the compressed stream.
        // If this attribute is accessed before the end of the stream
        // has been reached, its value will be b''.
        // TODO
        vm.ctx.new_bytes(b"".to_vec())
    }

    #[pyproperty]
    fn needs_input(&self, vm: &VirtualMachine) -> PyObjectRef {
        // False if the decompress() method can provide more
        // decompressed data before requiring new uncompressed input.
        // TODO
        let state = self.state.lock();
        vm.ctx.new_bool(state.needs_input)
    }

    // TODO: mro()?
}

fn _bz2_BZ2Decompressor(vm: &VirtualMachine) -> PyResult<BZ2Decompressor> {
    Ok(BZ2Decompressor {
        state: PyMutex::new(DecompressorState {
            eof: false,
            needs_input: true,
            unused_data: Vec::new(),
            decoder: Decoder::new(),
        }),
    })
}

struct CompressorState {
    flushed: bool,
    encoder: Option<BzEncoder<Vec<u8>>>,
}

#[pyclass(module = "_bz2", name = "BZ2Compressor")]
struct BZ2Compressor {
    state: PyMutex<CompressorState>,
}

impl fmt::Debug for BZ2Compressor {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "_bz2.BZ2Compressor")
    }
}

impl PyValue for BZ2Compressor {
    fn class(_vm: &VirtualMachine) -> &PyTypeRef {
        Self::static_type()
    }
}

// TODO: return partial results from compress() instead of returning everything in flush()
#[pyimpl]
impl BZ2Compressor {
    #[pymethod]
    fn compress(&self, data: PyBytesLike, vm: &VirtualMachine) -> PyResult {
        let mut state = self.state.lock();
        if state.flushed {
            return Err(vm.new_value_error("Compressor has been flushed".to_owned()));
        }

        let CompressorState { flushed, encoder } = &mut *state;

        // TODO: handle Err
        data.with_ref(|input_bytes| encoder.as_mut().unwrap().write_all(input_bytes).unwrap());
        Ok(vm.ctx.new_bytes(Vec::new()))
    }

    #[pymethod]
    fn flush(&self, vm: &VirtualMachine) -> PyResult {
        let mut state = self.state.lock();
        if state.flushed {
            return Err(vm.new_value_error("Repeated call to flush()".to_owned()));
        }

        let CompressorState { flushed, encoder } = &mut *state;

        // TODO: handle Err
        Ok(vm
            .ctx
            .new_bytes(encoder.take().unwrap().finish().unwrap().to_vec()))
    }
}

fn _bz2_BZ2Compressor(
    compresslevel: OptionalArg<i32>, // TODO: PyIntRef
    vm: &VirtualMachine,
) -> PyResult<BZ2Compressor> {
    // TODO: this library should use constants instead
    let compresslevel = compresslevel.unwrap_or(9);
    // compresslevel.unwrap_or(bzip2::Compression::best().level().try_into().unwrap());
    let level = match compresslevel {
        valid_level @ 1..=9 => bzip2::Compression::new(valid_level as u32),
        _ => return Err(vm.new_value_error("compresslevel must be between 1 and 9".to_owned())),
    };

    Ok(BZ2Compressor {
        state: PyMutex::new(CompressorState {
            flushed: false,
            encoder: Some(BzEncoder::new(Vec::new(), level)),
        }),
    })
}

pub fn make_module(vm: &VirtualMachine) -> PyObjectRef {
    let ctx = &vm.ctx;
    BZ2Decompressor::make_class(ctx);
    BZ2Compressor::make_class(ctx);

    py_module!(vm, "_bz2", {
        "BZ2Decompressor" => named_function!(ctx, _bz2, BZ2Decompressor),
        "BZ2Compressor" => named_function!(ctx, _bz2, BZ2Compressor),
    })
}
