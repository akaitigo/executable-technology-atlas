// SPDX-License-Identifier: Apache-2.0
@group(0) @binding(0) var<storage, read> input: array<vec3<f32>, 2>;
@group(0) @binding(1) var<storage, read_write> output: array<u32, 6>;
@compute @workgroup_size(1)
fn main() {
 let a = input[0]; let b = input[1];
 output[0] = bitcast<u32>(a.x); output[1] = bitcast<u32>(a.y); output[2] = bitcast<u32>(a.z);
 output[3] = bitcast<u32>(b.x); output[4] = bitcast<u32>(b.y); output[5] = bitcast<u32>(b.z);
}
