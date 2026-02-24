# HKSC-4096

HyperKnight Supercube Cryptosystem (16×16×16 = 4096 cells).

> Ghi chú: link Grok được cung cấp không truy cập được từ môi trường build (HTTP 403), nên phiên bản này triển khai đầy đủ một hệ HKSC-4096 khả dụng dựa trên đúng ý tưởng tên gọi: supercube 4096 ô + knight-walk + permutation/substitution nhiều vòng.

## Ý tưởng chính

- **Không gian trạng thái**: mỗi block có kích thước **4096 byte**, ánh xạ vào supercube `16x16x16`.
- **HyperKnight permutation**: tạo một hoán vị 4096 vị trí bằng **3D knight-walk có khóa** (Warnsdorff-like + keyed fallback).
- **Nhiều vòng mã hóa**:
  - Substitution: cộng `delta` theo vị trí/vòng/block rồi XOR với keystream SHA-256.
  - Permutation: phân tán byte theo đường đi HyperKnight.
- **Dẫn xuất khóa**: `scrypt(passphrase, salt)` để sinh master key.
- **Định dạng ciphertext**: `MAGIC | salt | nonce | rounds | original_len | body`.

## File chính

- `hksc4096.py`: thư viện và CLI (`encrypt` / `decrypt`).
- `tests/test_hksc4096.py`: kiểm thử round-trip và sai passphrase.

## Cách dùng CLI

```bash
python hksc4096.py encrypt -i plain.bin -o secret.hksc
python hksc4096.py decrypt -i secret.hksc -o recovered.bin
```

Có thể truyền passphrase qua tham số (kém an toàn hơn):

```bash
python hksc4096.py encrypt -i plain.bin -o secret.hksc -p "my-pass"
```

## Chạy test

```bash
python -m unittest discover -s tests -v
```

## Lưu ý an toàn

Đây là thiết kế **thực nghiệm**, chưa qua audit mật mã học độc lập. Không nên dùng cho dữ liệu tối mật trong production nếu chưa có đánh giá formal.
