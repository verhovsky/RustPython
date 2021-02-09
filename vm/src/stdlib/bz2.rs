use std::fmt;

use crate::builtins::pytype::PyTypeRef;
use crate::byteslike::PyBytesLike;
use crate::common::lock::PyMutex;
use crate::function::OptionalArg;
use crate::pyobject::{PyClassImpl, PyObjectRef, PyResult, PyValue, StaticType};
use crate::VirtualMachine;

struct DecompressorState {
    decompressor: bzip2::Decompress,
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
        // TODO: PyRefInt
        _max_length: OptionalArg<i32>,
        vm: &VirtualMachine,
    ) -> PyResult {
        let mut state = self.state.lock();
        let DecompressorState { decompressor } = &mut *state;

        data.with_ref(|data| {
            // TODO: need to resize?
            let mut out = Vec::new();

            // TODO: respect max_length
            // TODO: handle Err
            let status = decompressor.decompress_vec(data, &mut out).unwrap();
            println!("{:?}", status);
            Ok(vm.ctx.new_bytes(out))
        })
    }

    #[pyproperty]
    fn eof(&self, vm: &VirtualMachine) -> PyObjectRef {
        // True if the end-of-stream marker has been reached.
        // TODO
        vm.ctx.new_bool(true)
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
        vm.ctx.new_bool(false)
    }

    // TODO: mro()?
}

fn _bz2_BZ2Decompressor(vm: &VirtualMachine) -> PyResult<BZ2Decompressor> {
    Ok(BZ2Decompressor {
        state: PyMutex::new(DecompressorState {
            decompressor: bzip2::Decompress::new(false),
        }),
    })
}

struct CompressorState {
    flushed: bool,
    compressor: bzip2::Compress,
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

#[pyimpl]
impl BZ2Compressor {
    #[pymethod]
    fn compress(&self, data: PyBytesLike, vm: &VirtualMachine) -> PyResult {
        // TODO: error if flushed
        let mut state = self.state.lock();
        let CompressorState {
            flushed,
            compressor,
        } = &mut *state;

        // TODO: handle Err
        data.with_ref(|data| {
            // TODO: need to resize?
            let mut out = Vec::new();

            // TODO: respect max_length
            // TODO: handle Err
            let status = compressor
                .compress_vec(data, &mut out, bzip2::Action::Run)
                .unwrap();
            println!("{:?}", status);
            Ok(vm.ctx.new_bytes(out))
        })
    }

    #[pymethod]
    fn flush(&self, vm: &VirtualMachine) -> PyResult {
        let mut state = self.state.lock();
        let CompressorState {
            flushed,
            compressor,
        } = &mut *state;

        let mut out = Vec::new();
        // TODO: Flush or Finish?
        // TODO: handle Err
        let status = compressor
            .compress_vec(&[], &mut out, bzip2::Action::Flush)
            .unwrap();
        println!("{:?}", status);

        *flushed = true;

        Ok(vm.ctx.new_bytes(out))
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
        // TODO
        _ => return Err(vm.new_value_error("".to_owned())),
    };

    Ok(BZ2Compressor {
        state: PyMutex::new(CompressorState {
            flushed: false,
            compressor: bzip2::Compress::new(level, 30),
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
