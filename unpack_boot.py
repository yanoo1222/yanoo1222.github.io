#!/usr/bin/env python3
# Simple boot.img extractor for Android boot images

import struct
import os
import sys

def unpack_boot(boot_path, out_dir):
    """Extract kernel and ramdisk from boot.img"""
    os.makedirs(out_dir, exist_ok=True)
    
    with open(boot_path, 'rb') as f:
        data = f.read()
    
    # Check for ANDROID! magic (v0, v1, v2)
    if data[:8] == b'ANDROID!':
        print("[*] Found ANDROID! boot image")
        
        # Read header offsets
        # Structure: https://source.android.com/docs/core/architecture/bootloader/boot-image-header
        kernel_size = struct.unpack_from('<I', data, 8)[0]
        kernel_addr = struct.unpack_from('<I', data, 12)[0]
        ramdisk_size = struct.unpack_from('<I', data, 16)[0]
        ramdisk_addr = struct.unpack_from('<I', data, 20)[0]
        second_size = struct.unpack_from('<I', data, 24)[0]
        second_addr = struct.unpack_from('<I', data, 28)[0]
        tags_addr = struct.unpack_from('<I', data, 32)[0]
        page_size = struct.unpack_from('<I', data, 36)[0]
        
        print(f"[*] Kernel size: 0x{kernel_size:x}")
        print(f"[*] Ramdisk size: 0x{ramdisk_size:x}")
        print(f"[*] Page size: 0x{page_size:x}")
        
        # If page_size is 0, use default 4096
        if page_size == 0:
            print("[!] Page size is 0, using default 4096")
            page_size = 4096
        
        # Extract kernel (starts at page_size)
        kernel_offset = page_size
        kernel_data = data[kernel_offset:kernel_offset + kernel_size]
        
        kernel_path = os.path.join(out_dir, 'kernel')
        with open(kernel_path, 'wb') as f:
            f.write(kernel_data)
        print(f"[+] Kernel extracted to {kernel_path} (size: {len(kernel_data)} bytes)")
        
        # Extract ramdisk if present
        if ramdisk_size > 0:
            # Calculate ramdisk offset: header (1 page) + kernel pages
            kernel_pages = (kernel_size + page_size - 1) // page_size
            ramdisk_offset = page_size * (1 + kernel_pages)
            ramdisk_data = data[ramdisk_offset:ramdisk_offset + ramdisk_size]
            
            ramdisk_path = os.path.join(out_dir, 'ramdisk.cpio')
            with open(ramdisk_path, 'wb') as f:
                f.write(ramdisk_data)
            print(f"[+] Ramdisk extracted to {ramdisk_path}")
            
        # Extract second stage if present
        if second_size > 0:
            kernel_pages = (kernel_size + page_size - 1) // page_size
            ramdisk_pages = (ramdisk_size + page_size - 1) // page_size
            second_offset = page_size * (1 + kernel_pages + ramdisk_pages)
            second_data = data[second_offset:second_offset + second_size]
            
            second_path = os.path.join(out_dir, 'second')
            with open(second_path, 'wb') as f:
                f.write(second_data)
            print(f"[+] Second stage extracted to {second_path}")
            
    # Check for ANDR magic (v3, v4)
    elif data[:4] == b'ANDR':
        print("[*] Found ANDR boot image (v3+)")
        kernel_size = struct.unpack_from('<I', data, 8)[0]
        kernel_data = data[4096:4096 + kernel_size]
        
        kernel_path = os.path.join(out_dir, 'kernel')
        with open(kernel_path, 'wb') as f:
            f.write(kernel_data)
        print(f"[+] Kernel extracted to {kernel_path} (size: {len(kernel_data)} bytes)")
        
    else:
        print(f"[-] Unknown boot image format")
        print(f"    Magic: {data[:8]!r}")
        print(f"    Expected: ANDROID! or ANDR")
        return False
    
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 unpack_boot.py boot.img [output_dir]")
        print("")
        print("Example:")
        print("  python3 unpack_boot.py boot.img kernel_extracted/")
        sys.exit(1)
    
    boot_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "kernel_extracted"
    
    if not os.path.exists(boot_path):
        print(f"Error: {boot_path} not found")
        sys.exit(1)
    
    print(f"[*] Extracting from: {boot_path}")
    print(f"[*] Output directory: {out_dir}")
    
    success = unpack_boot(boot_path, out_dir)
    
    if success:
        print("[+] Done!")
    else:
        print("[-] Extraction failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
