#![feature(portable_simd)]

use pyo3::prelude::*;
use pyo3::types::PyBytes;
use rayon::prelude::*;
use std::sync::Arc;
use std::simd::{i32x4, u32x4, f32x4};
use std::simd::num::{SimdFloat, SimdInt};
use std::simd::cmp::SimdPartialEq;

/// Convert RGB -> RGB565
fn rgb_to_565(r: u8, g: u8, b: u8) -> u16 {
    (((r as u16 >> 3) << 11) | ((g as u16 >> 2) << 5) | (b as u16 >> 3)) as u16
}

fn unpack_565(c: u16) -> (u8, u8, u8) {
    let r = ((c >> 11) & 0x1F) as u8;
    let g = ((c >> 5) & 0x3F) as u8;
    let b = (c & 0x1F) as u8;
    ((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2))
}

/// Compute principal axis (3-vector) using power iteration on covariance of colors.
/// Input: list of RGB triples as f32 (0..255) - SIMD optimized
fn principal_axis_rgb(colors: &[(f32, f32, f32)]) -> (f32, f32, f32) {
    let n = colors.len() as f32;
    if colors.is_empty() { return (1.0, 0.0, 0.0); }

    // SIMD-accelerated mean computation
    let mut sum = f32x4::splat(0.0);
    let chunks = colors.chunks_exact(4);
    let remainder = chunks.remainder();
    
    for chunk in chunks {
        let r = f32x4::from_array([chunk[0].0, chunk[1].0, chunk[2].0, chunk[3].0]);
        let g = f32x4::from_array([chunk[0].1, chunk[1].1, chunk[2].1, chunk[3].1]);
        let b = f32x4::from_array([chunk[0].2, chunk[1].2, chunk[2].2, chunk[3].2]);
        sum += f32x4::from_array([r.reduce_sum(), g.reduce_sum(), b.reduce_sum(), 0.0]);
    }
    
    let mut mx = sum.as_array()[0];
    let mut my = sum.as_array()[1];
    let mut mz = sum.as_array()[2];
    
    // Handle remainder
    for &(x,y,z) in remainder {
        mx += x; my += y; mz += z;
    }
    mx /= n; my /= n; mz /= n;

    // compute covariance matrix (3x3) - SIMD optimized
    let mean = f32x4::from_array([mx, my, mz, 0.0]);
    let mut cxx = 0.0f32; let mut cxy = 0.0f32; let mut cxz = 0.0f32;
    let mut cyy = 0.0f32; let mut cyz = 0.0f32; let mut czz = 0.0f32;

    for &(x,y,z) in colors {
        let v = f32x4::from_array([x, y, z, 0.0]);
        let r = v - mean;
        let rx = r.as_array()[0];
        let ry = r.as_array()[1];
        let rz = r.as_array()[2];
        
        cxx += rx * rx;
        cxy += rx * ry;
        cxz += rx * rz;
        cyy += ry * ry;
        cyz += ry * rz;
        czz += rz * rz;
    }

    // power iteration: start with luminance-weighted vector for better convergence
    let mut v = f32x4::from_array([0.3f32, 0.59f32, 0.11f32, 0.0]);
    for _ in 0..16 {
        // multiply cov * v
        let vx = v.as_array()[0];
        let vy = v.as_array()[1];
        let vz = v.as_array()[2];
        
        let nx = cxx * vx + cxy * vy + cxz * vz;
        let ny = cxy * vx + cyy * vy + cyz * vz;
        let nz = cxz * vx + cyz * vy + czz * vz;
        
        let norm_sq = nx*nx + ny*ny + nz*nz;
        if norm_sq < 1e-20 { break; }
        let norm = norm_sq.sqrt();
        
        let new_v = f32x4::from_array([nx / norm, ny / norm, nz / norm, 0.0]);
        
        // Check convergence with SIMD
        let diff = (new_v - v).abs();
        let diff_sum = diff.as_array()[0] + diff.as_array()[1] + diff.as_array()[2];
        v = new_v;
        if diff_sum < 0.001 { break; }
    }
    (v.as_array()[0], v.as_array()[1], v.as_array()[2])
}

/// choose color endpoints via PCA projection and quantize to 565
fn choose_color_endpoints(block: &[[u8;4];16]) -> (u16,u16) {
    // collect rgb floats
    let cols: Vec<(f32, f32, f32)> = block.iter().map(|p| (p[0] as f32, p[1] as f32, p[2] as f32)).collect();
    let n = cols.len();
    // Method 1: PCA-based with inset optimization (NVTT3-style)
    let (ax, ay, az) = principal_axis_rgb(&cols);
    let mut min_proj = f32::INFINITY;
    let mut max_proj = f32::NEG_INFINITY;
    let mut min_col = (0u8,0u8,0u8);
    let mut max_col = (0u8,0u8,0u8);
    let mut min_proj_idx = 0;
    let mut max_proj_idx = 0;
    // SIMD vectorization for PCA projection
    let mut proj_arr = [0.0f32; 16];
    for i in (0..n).step_by(4) {
        let r = f32x4::from_array([
            cols.get(i).map_or(0.0, |c| c.0),
            cols.get(i+1).map_or(0.0, |c| c.0),
            cols.get(i+2).map_or(0.0, |c| c.0),
            cols.get(i+3).map_or(0.0, |c| c.0),
        ]);
        let g = f32x4::from_array([
            cols.get(i).map_or(0.0, |c| c.1),
            cols.get(i+1).map_or(0.0, |c| c.1),
            cols.get(i+2).map_or(0.0, |c| c.1),
            cols.get(i+3).map_or(0.0, |c| c.1),
        ]);
        let b = f32x4::from_array([
            cols.get(i).map_or(0.0, |c| c.2),
            cols.get(i+1).map_or(0.0, |c| c.2),
            cols.get(i+2).map_or(0.0, |c| c.2),
            cols.get(i+3).map_or(0.0, |c| c.2),
        ]);
        let proj = r * f32x4::splat(ax) + g * f32x4::splat(ay) + b * f32x4::splat(az);
        let arr = proj.as_array();
        for j in 0..4 {
            let idx = i + j;
            if idx < n {
                proj_arr[idx] = arr[j];
                if arr[j] < min_proj {
                    min_proj = arr[j];
                    min_proj_idx = idx;
                }
                if arr[j] > max_proj {
                    max_proj = arr[j];
                    max_proj_idx = idx;
                }
            }
        }
    }
    min_col = (cols[min_proj_idx].0 as u8, cols[min_proj_idx].1 as u8, cols[min_proj_idx].2 as u8);
    max_col = (cols[max_proj_idx].0 as u8, cols[max_proj_idx].1 as u8, cols[max_proj_idx].2 as u8);
    // NVTT3-style inset: move endpoints inward along principal axis
    let inset_shift = (max_proj - min_proj) / 16.0;
    if inset_shift > 0.0 {
        min_proj += inset_shift;
        max_proj -= inset_shift;
        let mut best_min_err = f32::INFINITY;
        let mut best_max_err = f32::INFINITY;
        for i in 0..n {
            let proj = proj_arr[i];
            let min_err = (proj - min_proj).abs();
            if min_err < best_min_err {
                best_min_err = min_err;
                min_col = (cols[i].0 as u8, cols[i].1 as u8, cols[i].2 as u8);
            }
            let max_err = (proj - max_proj).abs();
            if max_err < best_max_err {
                best_max_err = max_err;
                max_col = (cols[i].0 as u8, cols[i].1 as u8, cols[i].2 as u8);
            }
        }
    }
    let pca_c0 = rgb_to_565(max_col.0, max_col.1, max_col.2);
    let pca_c1 = rgb_to_565(min_col.0, min_col.1, min_col.2);
    // Method 2: Bounding box (min/max per channel)
    let mut min_r = 255u8; let mut max_r = 0u8;
    let mut min_g = 255u8; let mut max_g = 0u8;
    let mut min_b = 255u8; let mut max_b = 0u8;
    for &(r,g,b) in &cols {
        let ri = r as u8; let gi = g as u8; let bi = b as u8;
        min_r = min_r.min(ri); max_r = max_r.max(ri);
        min_g = min_g.min(gi); max_g = max_g.max(gi);
        min_b = min_b.min(bi); max_b = max_b.max(bi);
    }
    let bbox_c0 = rgb_to_565(max_r, max_g, max_b);
    let bbox_c1 = rgb_to_565(min_r, min_g, min_b);
    // Method 3: Luminance-based extremes (SIMD)
    let mut min_lum = f32::INFINITY; let mut max_lum = f32::NEG_INFINITY;
    let mut min_lum_idx = 0; let mut max_lum_idx = 0;
    for i in (0..n).step_by(4) {
        let r = f32x4::from_array([
            cols.get(i).map_or(0.0, |c| c.0),
            cols.get(i+1).map_or(0.0, |c| c.0),
            cols.get(i+2).map_or(0.0, |c| c.0),
            cols.get(i+3).map_or(0.0, |c| c.0),
        ]);
        let g = f32x4::from_array([
            cols.get(i).map_or(0.0, |c| c.1),
            cols.get(i+1).map_or(0.0, |c| c.1),
            cols.get(i+2).map_or(0.0, |c| c.1),
            cols.get(i+3).map_or(0.0, |c| c.1),
        ]);
        let b = f32x4::from_array([
            cols.get(i).map_or(0.0, |c| c.2),
            cols.get(i+1).map_or(0.0, |c| c.2),
            cols.get(i+2).map_or(0.0, |c| c.2),
            cols.get(i+3).map_or(0.0, |c| c.2),
        ]);
        let lum = r * f32x4::splat(0.3) + g * f32x4::splat(0.59) + b * f32x4::splat(0.11);
        let arr = lum.as_array();
        for j in 0..4 {
            let idx = i + j;
            if idx < n {
                if arr[j] < min_lum {
                    min_lum = arr[j];
                    min_lum_idx = idx;
                }
                if arr[j] > max_lum {
                    max_lum = arr[j];
                    max_lum_idx = idx;
                }
            }
        }
    }
    let min_lum_col = (cols[min_lum_idx].0 as u8, cols[min_lum_idx].1 as u8, cols[min_lum_idx].2 as u8);
    let max_lum_col = (cols[max_lum_idx].0 as u8, cols[max_lum_idx].1 as u8, cols[max_lum_idx].2 as u8);
    let lum_c0 = rgb_to_565(max_lum_col.0, max_lum_col.1, max_lum_col.2);
    let lum_c1 = rgb_to_565(min_lum_col.0, min_lum_col.1, min_lum_col.2);
    // Test all three methods and pick the best
    let candidates = [(pca_c0, pca_c1), (bbox_c0, bbox_c1), (lum_c0, lum_c1)];
    let mut best = candidates[0];
    let mut best_err = total_block_error(block, best.0, best.1);
    for &(c0, c1) in &candidates[1..] {
        let err = total_block_error(block, c0, c1);
        if err < best_err {
            best_err = err;
            best = (c0, c1);
        }
    }
    let mut c0 = best.0;
    let mut c1 = best.1;
    // Heuristic: if endpoints are equal after quantize, perturb slightly
    if c0 == c1 {
        let (r0,g0,b0) = max_col;
        let (r1,g1,b1) = min_col;
        if r0 != 255 { c0 = rgb_to_565(r0+1, g0, b0); }
        else if g0 != 255 { c0 = rgb_to_565(r0, g0+1, b0); }
        else if b0 != 255 { c0 = rgb_to_565(r0, g0, b0+1); }
        else if r1 != 0 { c1 = rgb_to_565(r1-1, g1, b1); }
    }
    (c0, c1)
}

/// generate palette for DXT1 (given unpacked 565 -> rgb888)
#[inline]
fn palette_from_endpoints(c0: u16, c1: u16) -> [(u8,u8,u8,u8);4] {
    let (r0,g0,b0) = unpack_565(c0);
    let (r1,g1,b1) = unpack_565(c1);
    let mut palette = [(0u8,0u8,0u8,255u8);4];
    palette[0] = (r0,g0,b0,255);
    palette[1] = (r1,g1,b1,255);
    if c0 > c1 {
        palette[2] = (
            ((2*r0 as u16 + r1 as u16) / 3) as u8,
            ((2*g0 as u16 + g1 as u16) / 3) as u8,
            ((2*b0 as u16 + b1 as u16) / 3) as u8,
            255
        );
        palette[3] = (
            ((r0 as u16 + 2*r1 as u16) / 3) as u8,
            ((g0 as u16 + 2*g1 as u16) / 3) as u8,
            ((b0 as u16 + 2*b1 as u16) / 3) as u8,
            255
        );
    } else {
        palette[2] = (
            (((r0 as u16 + r1 as u16) / 2) as u8),
            (((g0 as u16 + g1 as u16) / 2) as u8),
            (((b0 as u16 + b1 as u16) / 2) as u8),
            255
        );
        palette[3] = (0,0,0,0); // transparent
    }
    palette
}

/// pack 16 2-bit indices (LSB first per pixel index) into u32 with perceptual weighting - SIMD optimized
fn choose_color_indices(block: &[[u8;4];16], palette: &[(u8,u8,u8,u8);4]) -> u32 {
    let mut bits = 0u32;
    
    // Precompute palette in SIMD-friendly format
    let pal_r = i32x4::from_array([palette[0].0 as i32, palette[1].0 as i32, palette[2].0 as i32, palette[3].0 as i32]);
    let pal_g = i32x4::from_array([palette[0].1 as i32, palette[1].1 as i32, palette[2].1 as i32, palette[3].1 as i32]);
    let pal_b = i32x4::from_array([palette[0].2 as i32, palette[1].2 as i32, palette[2].2 as i32, palette[3].2 as i32]);
    let pal_a = u32x4::from_array([palette[0].3 as u32, palette[1].3 as u32, palette[2].3 as u32, palette[3].3 as u32]);
    
    const WEIGHT_R: i32 = 30;
    const WEIGHT_G: i32 = 59;
    const WEIGHT_B: i32 = 11;
    let weight_r = i32x4::splat(WEIGHT_R);
    let weight_g = i32x4::splat(WEIGHT_G);
    let weight_b = i32x4::splat(WEIGHT_B);
    
    for i in 0..16 {
        let px = block[i];
        let px_r = i32x4::splat(px[0] as i32);
        let px_g = i32x4::splat(px[1] as i32);
        let px_b = i32x4::splat(px[2] as i32);
        
        // Calculate differences for all 4 palette entries at once
        let dr = px_r - pal_r;
        let dg = px_g - pal_g;
        let db = px_b - pal_b;
        
        // Perceptual error calculation
        let err = (dr * dr * weight_r + dg * dg * weight_g + db * db * weight_b).cast::<u32>();
        
        // Handle transparent preference
        let err_adjusted = if px[3] < 128 {
            let transparent_mask = pal_a.simd_eq(u32x4::splat(0));
            transparent_mask.select(u32x4::splat(0), err)
        } else {
            err
        };
        
        // Find minimum error index
        let err_array = err_adjusted.as_array();
        let mut best = 0usize;
        let mut best_err = err_array[0];
        for j in 1..4 {
            if err_array[j] < best_err {
                best_err = err_array[j];
                best = j;
            }
        }
        bits |= (best as u32) << (i * 2);
    }
    bits
}

/// Calculate total perceptual error for a block given endpoints - SIMD optimized
#[inline]
fn total_block_error(block: &[[u8;4];16], c0: u16, c1: u16) -> u32 {
    let palette = palette_from_endpoints(c0, c1);
    
    // Precompute palette in SIMD-friendly format
    let pal_r = i32x4::from_array([palette[0].0 as i32, palette[1].0 as i32, palette[2].0 as i32, palette[3].0 as i32]);
    let pal_g = i32x4::from_array([palette[0].1 as i32, palette[1].1 as i32, palette[2].1 as i32, palette[3].1 as i32]);
    let pal_b = i32x4::from_array([palette[0].2 as i32, palette[1].2 as i32, palette[2].2 as i32, palette[3].2 as i32]);
    let pal_a = u32x4::from_array([palette[0].3 as u32, palette[1].3 as u32, palette[2].3 as u32, palette[3].3 as u32]);
    
    const WEIGHT_R: i32 = 30;
    const WEIGHT_G: i32 = 59;
    const WEIGHT_B: i32 = 11;
    let weight_r = i32x4::splat(WEIGHT_R);
    let weight_g = i32x4::splat(WEIGHT_G);
    let weight_b = i32x4::splat(WEIGHT_B);
    
    let mut total_err = 0u32;
    
    for px in block {
        let px_r = i32x4::splat(px[0] as i32);
        let px_g = i32x4::splat(px[1] as i32);
        let px_b = i32x4::splat(px[2] as i32);
        
        // Calculate differences for all 4 palette entries at once
        let dr = px_r - pal_r;
        let dg = px_g - pal_g;
        let db = px_b - pal_b;
        
        // Perceptual error calculation
        let err = (dr * dr * weight_r + dg * dg * weight_g + db * db * weight_b).cast::<u32>();
        
        // Handle transparent preference
        let err_adjusted = if px[3] < 128 {
            let transparent_mask = pal_a.simd_eq(u32x4::splat(0));
            transparent_mask.select(u32x4::splat(0), err)
        } else {
            err
        };
        
        // Find minimum error
        let err_array = err_adjusted.as_array();
        let best_err = err_array[0].min(err_array[1]).min(err_array[2]).min(err_array[3]);
        total_err += best_err;
    }
    total_err
}

/// Adjust RGB565 value by delta in each component (clamped)
#[inline(always)]
fn adjust_565(c: u16, dr: i32, dg: i32, db: i32) -> u16 {
    let r = ((c >> 11) & 0x1F) as i32;
    let g = ((c >> 5) & 0x3F) as i32;
    let b = (c & 0x1F) as i32;
    
    let new_r = (r + dr).clamp(0, 31) as u16;
    let new_g = (g + dg).clamp(0, 63) as u16;
    let new_b = (b + db).clamp(0, 31) as u16;
    
    (new_r << 11) | (new_g << 5) | new_b
}

/// Refine endpoints by testing small adjustments - NVTT3-style with larger search and better convergence
fn refine_endpoints(block: &[[u8;4];16], c0: u16, c1: u16) -> (u16, u16) {
    let mut best_c0 = c0;
    let mut best_c1 = c1;
    let mut best_err = total_block_error(block, c0, c1);
    
    // Early exit if error is already very small
    if best_err < 16 { return (best_c0, best_c1); }
    
    // NVTT3 uses iterative refinement with larger search radius
    // Multiple passes with decreasing search radius for better convergence
    
    // Pass 1: Large search radius (±2)
    for dr in -2i32..=2 {
        for dg in -2i32..=2 {
            for db in -2i32..=2 {
                if dr == 0 && dg == 0 && db == 0 { continue; }
                let new_c0 = adjust_565(c0, dr, dg, db);
                let err = total_block_error(block, new_c0, best_c1);
                if err < best_err {
                    best_err = err;
                    best_c0 = new_c0;
                }
            }
        }
    }
    
    for dr in -2i32..=2 {
        for dg in -2i32..=2 {
            for db in -2i32..=2 {
                if dr == 0 && dg == 0 && db == 0 { continue; }
                let new_c1 = adjust_565(c1, dr, dg, db);
                let err = total_block_error(block, best_c0, new_c1);
                if err < best_err {
                    best_err = err;
                    best_c1 = new_c1;
                }
            }
        }
    }
    
    // Pass 2: Fine-tune with small radius (±1) from improved endpoints
    let pass1_c0 = best_c0;
    let pass1_c1 = best_c1;
    
    for dr in -1i32..=1 {
        for dg in -1i32..=1 {
            for db in -1i32..=1 {
                if dr == 0 && dg == 0 && db == 0 { continue; }
                let new_c0 = adjust_565(pass1_c0, dr, dg, db);
                let err = total_block_error(block, new_c0, best_c1);
                if err < best_err {
                    best_err = err;
                    best_c0 = new_c0;
                }
            }
        }
    }
    
    for dr in -1i32..=1 {
        for dg in -1i32..=1 {
            for db in -1i32..=1 {
                if dr == 0 && dg == 0 && db == 0 { continue; }
                let new_c1 = adjust_565(pass1_c1, dr, dg, db);
                let err = total_block_error(block, best_c0, new_c1);
                if err < best_err {
                    best_err = err;
                    best_c1 = new_c1;
                }
            }
        }
    }
    
    // Pass 3: Joint optimization - test both endpoints together for final refinement
    let pass2_c0 = best_c0;
    let pass2_c1 = best_c1;
    
    for dr0 in -1i32..=1 {
        for dg0 in -1i32..=1 {
            for db0 in -1i32..=1 {
                for dr1 in -1i32..=1 {
                    for dg1 in -1i32..=1 {
                        for db1 in -1i32..=1 {
                            if (dr0 == 0 && dg0 == 0 && db0 == 0) && (dr1 == 0 && dg1 == 0 && db1 == 0) { continue; }
                            let new_c0 = adjust_565(pass2_c0, dr0, dg0, db0);
                            let new_c1 = adjust_565(pass2_c1, dr1, dg1, db1);
                            let err = total_block_error(block, new_c0, new_c1);
                            if err < best_err {
                                best_err = err;
                                best_c0 = new_c0;
                                best_c1 = new_c1;
                            }
                        }
                    }
                }
            }
        }
    }
    
    (best_c0, best_c1)
}

/// compress one block into DXT1 (8 bytes)
fn compress_block_dxt1(block: &[[u8;4];16]) -> [u8;8] {
    let (mut c0, mut c1) = choose_color_endpoints(block);
    // Refine endpoints for better quality
    let (rc0, rc1) = refine_endpoints(block, c0, c1);
    c0 = rc0;
    c1 = rc1;
    // If any pixel alpha < 128, ensure we pick the 1-bit alpha mode if beneficial.
    let any_transparent = block.iter().any(|p| p[3] < 128);
    if any_transparent && c0 > c1 {
        std::mem::swap(&mut c0, &mut c1);
    }
    let palette = palette_from_endpoints(c0, c1);
    let idx_bits = choose_color_indices(block, &palette);
    let mut out = [0u8;8];
    out[0] = (c0 & 0xFF) as u8;
    out[1] = (c0 >> 8) as u8;
    out[2] = (c1 & 0xFF) as u8;
    out[3] = (c1 >> 8) as u8;
    out[4] = (idx_bits & 0xFF) as u8;
    out[5] = ((idx_bits >> 8) & 0xFF) as u8;
    out[6] = ((idx_bits >> 16) & 0xFF) as u8;
    out[7] = ((idx_bits >> 24) & 0xFF) as u8;
    out
}

/// DXT3 alpha packing: explicit 4-bit per pixel in block order (row-major). 64 bits (8 bytes) for alpha.
fn pack_dxt3_alpha(block: &[[u8;4];16]) -> [u8;8] {
    let mut alpha_u64: u64 = 0;
    // DXT3 stores 4-bit alpha per pixel; order is row-major, each 4 bits; pack little-endian into 64-bit
    for i in 0..16 {
        let a4 = (block[i][3] as u32 * 15 + 127) / 255; // convert 0..255 -> 0..15 with rounding
        alpha_u64 |= (a4 as u64) << (i * 4);
    }
    let mut out = [0u8;8];
    out[0] = (alpha_u64 & 0xFF) as u8;
    out[1] = ((alpha_u64 >> 8) & 0xFF) as u8;
    out[2] = ((alpha_u64 >> 16) & 0xFF) as u8;
    out[3] = ((alpha_u64 >> 24) & 0xFF) as u8;
    out[4] = ((alpha_u64 >> 32) & 0xFF) as u8;
    out[5] = ((alpha_u64 >> 40) & 0xFF) as u8;
    out[6] = ((alpha_u64 >> 48) & 0xFF) as u8;
    out[7] = ((alpha_u64 >> 56) & 0xFF) as u8;
    out
}

/// Choose alpha endpoints for DXT5 using percentile-based selection for better quality.
/// Returns (alpha0, alpha1, 48-bit packed indices as u64 (lower 48 bits contain 3-bit indices packed)).
fn compress_block_dxt5_alpha(block: &[[u8;4];16]) -> (u8,u8,u64) {
    // Gather alphas and sort for percentile selection
    let mut sorted_alphas: Vec<u8> = block.iter().map(|p| p[3]).collect();
    sorted_alphas.sort_unstable();
    
    // Use percentiles instead of hard min/max to avoid outliers
    // 93rd percentile (index 14) and 7th percentile (index 1)
    let mut a0 = sorted_alphas[14].max(sorted_alphas[15].saturating_sub(1));
    let mut a1 = sorted_alphas[1].min(sorted_alphas[0].saturating_add(1));
    
    // Try to avoid equal endpoints
    if a0 == a1 {
        if a0 == 255 { a1 = 254; } else { a0 = a1 + 1; }
    }

    // build 8-entry alpha palette
    let mut pal = [0u8;8];
    pal[0] = a0;
    pal[1] = a1;
    if a0 > a1 {
        // 6 interpolated
        for i in 1..6 {
            pal[i+1] = ((( (6 - i) as u16 * a0 as u16 + i as u16 * a1 as u16) / 6) & 0xFF) as u8;
        }
    } else {
        // 4 interpolated, then 0 and 255
        for i in 1..4 {
            pal[i+1] = ((((4 - i) as u16 * a0 as u16 + i as u16 * a1 as u16) / 4) & 0xFF) as u8;
        }
        pal[6] = 0;
        pal[7] = 255;
    }

    // choose 3-bit indices for 16 pixels
    let mut index_bits: u64 = 0;
    for i in 0..16 {
        let a = block[i][3];
        // find closest palette entry by squared error
        let mut best = 0usize;
        let mut best_err = u32::MAX;
        for j in 0..8 {
            let diff = a as i32 - pal[j] as i32;
            let err = (diff*diff) as u32;
            if err < best_err { best_err = err; best = j; }
        }
        // pack 3 bits per pixel, starting with pixel 0 in least significant bits
        index_bits |= (best as u64) << (i * 3);
    }
    (a0, a1, index_bits)
}

/// DXT5 alpha block packing: alpha0 (u8), alpha1 (u8), then 6 bytes for 16*3bits indexes.
fn pack_dxt5_alpha(a0: u8, a1: u8, indices: u64) -> [u8;8] {
    let mut out = [0u8;8];
    out[0] = a0;
    out[1] = a1;
    // indices uses lower 48 bits
    out[2] = (indices & 0xFF) as u8;
    out[3] = ((indices >> 8) & 0xFF) as u8;
    out[4] = ((indices >> 16) & 0xFF) as u8;
    out[5] = ((indices >> 24) & 0xFF) as u8;
    out[6] = ((indices >> 32) & 0xFF) as u8;
    out[7] = ((indices >> 40) & 0xFF) as u8;
    out
}

/// Helper: read block of 4x4 from image bytes (RGBA u8) with edge-clamp for incomplete blocks
fn read_block_clamp(rgba: &[u8], width: usize, height: usize, bx: usize, by: usize) -> [[u8;4];16] {
    let mut out = [[0u8;4];16];
    for row in 0..4 {
        for col in 0..4 {
            let sx = (bx + col).min(width - 1);
            let sy = (by + row).min(height - 1);
            let idx = (sy * width + sx) * 4;
            out[row * 4 + col] = [rgba[idx], rgba[idx+1], rgba[idx+2], rgba[idx+3]];
        }
    }
    out
}


/// Top-level compressor for DXT3 (alpha explicit 4-bit + DXT1 color)
#[pyfunction]
fn compress_dxt3(py: Python<'_>, rgba: Vec<u8>, width: usize, height: usize) -> PyResult<PyObject> {
    if rgba.len() != width * height * 4 {
        return Err(pyo3::exceptions::PyValueError::new_err("Invalid RGBA size"));
    }
    let blocks_x = (width + 3) / 4;
    let blocks_y = (height + 3) / 4;
    let total = blocks_x * blocks_y;
    
    let rgba = Arc::new(rgba);
    // Release GIL while doing CPU work in parallel
    let out = py.allow_threads(|| {
        // Process blocks in parallel
        let blocks: Vec<[u8;16]> = (0..total).into_par_iter().map(|i| {
            let bx = (i % blocks_x) * 4;
            let by = (i / blocks_x) * 4;
            let block = read_block_clamp(&rgba, width, height, bx, by);
            let alpha_bytes = pack_dxt3_alpha(&block);
            let color_bytes = compress_block_dxt1(&block);
            
            let mut result = [0u8;16];
            result[0..8].copy_from_slice(&alpha_bytes);
            result[8..16].copy_from_slice(&color_bytes);
            result
        }).collect();
        
        // Flatten into output buffer
        let mut out = Vec::with_capacity(total * 16);
        for b in blocks {
            out.extend_from_slice(&b);
        }
        out
    });
    
    Ok(PyBytes::new(py, &out).into())
}

/// Top-level compressor for DXT5 (alpha interpolated + color block)
#[pyfunction]
fn compress_dxt5(py: Python<'_>, rgba: Vec<u8>, width: usize, height: usize) -> PyResult<PyObject> {
    if rgba.len() != width * height * 4 {
        return Err(pyo3::exceptions::PyValueError::new_err("Invalid RGBA size"));
    }
    let blocks_x = (width + 3) / 4;
    let blocks_y = (height + 3) / 4;
    let total = blocks_x * blocks_y;
    
    let rgba = Arc::new(rgba);
    // Release GIL while doing CPU work in parallel
    let out = py.allow_threads(|| {
        // Process blocks in parallel
        let blocks: Vec<[u8;16]> = (0..total).into_par_iter().map(|i| {
            let bx = (i % blocks_x) * 4;
            let by = (i / blocks_x) * 4;
            let block = read_block_clamp(&rgba, width, height, bx, by);
            let (a0, a1, aidxs) = compress_block_dxt5_alpha(&block);
            let alpha_bytes = pack_dxt5_alpha(a0, a1, aidxs);
            let color_bytes = compress_block_dxt1(&block);
            
            let mut result = [0u8;16];
            result[0..8].copy_from_slice(&alpha_bytes);
            result[8..16].copy_from_slice(&color_bytes);
            result
        }).collect();
        
        // Flatten into output buffer
        let mut out = Vec::with_capacity(total * 16);
        for b in blocks {
            out.extend_from_slice(&b);
        }
        out
    });
    
    Ok(PyBytes::new(py, &out).into())
}

/// Decompress DXT1 to RGBA
#[pyfunction]
fn decompress_dxt1(py: Python<'_>, data: Vec<u8>, width: usize, height: usize) -> PyResult<PyObject> {
    let out = py.allow_threads(|| {
        decompress_bc1_blocks(&data, width, height)
    });
    
    Ok(PyBytes::new(py, &out).into())
}

/// Decompress DXT3 to RGBA
#[pyfunction]
fn decompress_dxt3(py: Python<'_>, data: Vec<u8>, width: usize, height: usize) -> PyResult<PyObject> {
    let out = py.allow_threads(|| {
        decompress_dxt3_blocks(&data, width, height)
    });
    
    Ok(PyBytes::new(py, &out).into())
}

/// Decompress DXT5 to RGBA
#[pyfunction]
fn decompress_dxt5(py: Python<'_>, data: Vec<u8>, width: usize, height: usize) -> PyResult<PyObject> {
    let out = py.allow_threads(|| {
        decompress_bc3_blocks(&data, width, height)
    });
    
    Ok(PyBytes::new(py, &out).into())
}

/// Helper: Decompress BC1/DXT1 block
fn decompress_bc1_block(block_data: &[u8]) -> [[u8;4];16] {
    let c0 = u16::from_le_bytes([block_data[0], block_data[1]]);
    let c1 = u16::from_le_bytes([block_data[2], block_data[3]]);
    let indices = u32::from_le_bytes([block_data[4], block_data[5], block_data[6], block_data[7]]);
    
    let palette = palette_from_endpoints(c0, c1);
    
    let mut pixels = [[0u8;4];16];
    for i in 0..16 {
        let idx = ((indices >> (i * 2)) & 0x3) as usize;
        pixels[i] = [palette[idx].0, palette[idx].1, palette[idx].2, palette[idx].3];
    }
    pixels
}

/// Helper: Decompress DXT3 alpha block (explicit 4-bit alpha)
fn decompress_dxt3_alpha_block(block_data: &[u8]) -> [u8;16] {
    let mut alphas = [0u8;16];
    let alpha_u64 = u64::from_le_bytes([
        block_data[0], block_data[1], block_data[2], block_data[3],
        block_data[4], block_data[5], block_data[6], block_data[7]
    ]);
    
    for i in 0..16 {
        let a4 = ((alpha_u64 >> (i * 4)) & 0xF) as u8;
        // Convert 4-bit (0..15) back to 8-bit (0..255)
        alphas[i] = (a4 * 255 + 7) / 15;
    }
    alphas
}

/// Helper: Decompress BC3/DXT5 alpha block
fn decompress_bc3_alpha_block(block_data: &[u8]) -> [u8;16] {
    let a0 = block_data[0];
    let a1 = block_data[1];
    
    let mut palette = [0u8;8];
    palette[0] = a0;
    palette[1] = a1;
    
    if a0 > a1 {
        for i in 1..=6 {
            palette[i+1] = (((7-i) as u16 * a0 as u16 + i as u16 * a1 as u16) / 7) as u8;
        }
    } else {
        for i in 1..=4 {
            palette[i+1] = (((5-i) as u16 * a0 as u16 + i as u16 * a1 as u16) / 5) as u8;
        }
        palette[6] = 0;
        palette[7] = 255;
    }
    
    let mut indices = 0u64;
    for i in 0..6 {
        indices |= (block_data[2+i] as u64) << (i * 8);
    }
    
    let mut alphas = [0u8;16];
    for i in 0..16 {
        let idx = ((indices >> (i * 3)) & 0x7) as usize;
        alphas[i] = palette[idx];
    }
    alphas
}

/// Decompress BC1 blocks to RGBA
fn decompress_bc1_blocks(data: &[u8], width: usize, height: usize) -> Vec<u8> {
    let blocks_x = (width + 3) / 4;
    let blocks_y = (height + 3) / 4;
    let mut rgba = vec![0u8; width * height * 4];
    
    for by in 0..blocks_y {
        for bx in 0..blocks_x {
            let block_idx = by * blocks_x + bx;
            let block_data = &data[block_idx * 8..(block_idx + 1) * 8];
            let pixels = decompress_bc1_block(block_data);
            
            for py in 0..4 {
                for px in 0..4 {
                    let x = bx * 4 + px;
                    let y = by * 4 + py;
                    if x < width && y < height {
                        let dst_idx = (y * width + x) * 4;
                        let src_idx = py * 4 + px;
                        rgba[dst_idx..dst_idx+4].copy_from_slice(&pixels[src_idx]);
                    }
                }
            }
        }
    }
    rgba
}

/// Decompress DXT3 blocks to RGBA
fn decompress_dxt3_blocks(data: &[u8], width: usize, height: usize) -> Vec<u8> {
    let blocks_x = (width + 3) / 4;
    let blocks_y = (height + 3) / 4;
    let mut rgba = vec![0u8; width * height * 4];
    
    for by in 0..blocks_y {
        for bx in 0..blocks_x {
            let block_idx = by * blocks_x + bx;
            let block_data = &data[block_idx * 16..(block_idx + 1) * 16];
            
            let alphas = decompress_dxt3_alpha_block(&block_data[0..8]);
            let pixels = decompress_bc1_block(&block_data[8..16]);
            
            for py in 0..4 {
                for px in 0..4 {
                    let x = bx * 4 + px;
                    let y = by * 4 + py;
                    if x < width && y < height {
                        let dst_idx = (y * width + x) * 4;
                        let src_idx = py * 4 + px;
                        rgba[dst_idx] = pixels[src_idx][0];
                        rgba[dst_idx+1] = pixels[src_idx][1];
                        rgba[dst_idx+2] = pixels[src_idx][2];
                        rgba[dst_idx+3] = alphas[src_idx];
                    }
                }
            }
        }
    }
    rgba
}

/// Decompress BC3 blocks to RGBA
fn decompress_bc3_blocks(data: &[u8], width: usize, height: usize) -> Vec<u8> {
    let blocks_x = (width + 3) / 4;
    let blocks_y = (height + 3) / 4;
    let mut rgba = vec![0u8; width * height * 4];
    
    for by in 0..blocks_y {
        for bx in 0..blocks_x {
            let block_idx = by * blocks_x + bx;
            let block_data = &data[block_idx * 16..(block_idx + 1) * 16];
            
            let alphas = decompress_bc3_alpha_block(&block_data[0..8]);
            let pixels = decompress_bc1_block(&block_data[8..16]);
            
            for py in 0..4 {
                for px in 0..4 {
                    let x = bx * 4 + px;
                    let y = by * 4 + py;
                    if x < width && y < height {
                        let dst_idx = (y * width + x) * 4;
                        let src_idx = py * 4 + px;
                        rgba[dst_idx] = pixels[src_idx][0];
                        rgba[dst_idx+1] = pixels[src_idx][1];
                        rgba[dst_idx+2] = pixels[src_idx][2];
                        rgba[dst_idx+3] = alphas[src_idx];
                    }
                }
            }
        }
    }
    rgba
}

/// Python module
#[pymodule]
fn blockCompressor(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(compress_dxt1, m)?)?;
    m.add_function(wrap_pyfunction!(compress_dxt3, m)?)?;
    m.add_function(wrap_pyfunction!(compress_dxt5, m)?)?;
    
    m.add_function(wrap_pyfunction!(decompress_dxt1, m)?)?;
    m.add_function(wrap_pyfunction!(decompress_dxt3, m)?)?;
    m.add_function(wrap_pyfunction!(decompress_dxt5, m)?)?;
    
    Ok(())
}