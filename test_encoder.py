#!/usr/bin/env python3
"""
单元测试脚本
测试邮件编码器的核心功能
"""

from email_encoder import create_encoder

def test_basic_encoding():
    """测试基本的消息编码和解码"""
    print("测试1: 基本消息编码/解码...")
    encoder = create_encoder("test_secret", "ua_001")
    
    # 测试消息编码
    encoded = encoder.encode_secure_message("Hello World")
    assert encoded['secure'] == True
    assert encoded['sequence'] == 1
    assert encoded['ua_identity'] == "ua_001"
    
    # 测试消息解码
    decoded, verified, msg_type = encoder.decode_secure_message(encoded)
    assert decoded == "Hello World"
    assert verified == True
    assert msg_type == "paired"
    
    print("✓ 基本编码/解码测试通过")

def test_chinese_encoding():
    """测试中文内容编码"""
    print("测试2: 中文内容编码/解码...")
    encoder = create_encoder("test_secret", "ua_001")
    
    chinese_text = "你好，世界！这是一封加密邮件。"
    encoded = encoder.encode_secure_message(chinese_text)
    decoded, verified, msg_type = encoder.decode_secure_message(encoded)
    
    assert decoded == chinese_text
    assert verified == True
    
    print("✓ 中文编码/解码测试通过")

def test_attachment_encoding():
    """测试附件编码和解码"""
    print("测试3: 附件编码/解码...")
    encoder = create_encoder("test_secret", "ua_001")
    
    # 测试附件编码
    test_data = b"Test file content with some binary data: \x00\x01\x02"
    encoded = encoder.encode_attachment(test_data, "test.txt")
    assert encoded['secure'] == True
    assert encoded['filename'] == "test.txt"
    
    # 测试附件解码
    decoded, verified, msg_type = encoder.decode_attachment(encoded)
    assert decoded == test_data
    assert verified == True
    assert msg_type == "paired"
    
    print("✓ 附件编码/解码测试通过")

def test_ua_identity():
    """测试UA身份识别"""
    print("测试4: UA身份识别...")
    encoder_a = create_encoder("test_secret", "ua_001")
    encoder_b = create_encoder("test_secret", "ua_002")
    
    # A编码
    encoded = encoder_a.encode_secure_message("Secret message")
    
    # B尝试解码（不同的UA身份）
    decoded, verified, msg_type = encoder_b.decode_secure_message(encoded)
    assert msg_type == "other_ua"
    assert verified == False
    assert "无法解密" in decoded or "其他UA" in decoded
    
    # 测试配对UA的情况
    encoder_c = create_encoder("test_secret", "ua_001")  # 相同的UA身份
    encoded2 = encoder_a.encode_secure_message("Secret message 2")
    decoded2, verified2, msg_type2 = encoder_c.decode_secure_message(encoded2)
    assert msg_type2 == "paired"
    assert verified2 == True
    assert decoded2 == "Secret message 2"
    
    print("✓ UA身份识别测试通过")

def test_one_time_pad():
    """测试一次一密特性"""
    print("测试5: 一次一密（序列号递增）...")
    encoder = create_encoder("test_secret", "ua_001")
    
    # 发送多封邮件，每封应该使用不同的序列号
    encoded1 = encoder.encode_secure_message("Message 1")
    encoded2 = encoder.encode_secure_message("Message 2")
    encoded3 = encoder.encode_secure_message("Message 3")
    
    assert encoded1['sequence'] == 1
    assert encoded2['sequence'] == 2
    assert encoded3['sequence'] == 3
    
    # 即使是相同的消息内容，不同序列号也会产生不同的编码
    encoded_same_1 = encoder.encode_secure_message("Same message")
    encoded_same_2 = encoder.encode_secure_message("Same message")
    assert encoded_same_1['sequence'] != encoded_same_2['sequence']
    assert encoded_same_1['content'] != encoded_same_2['content']  # 不同序列号，编码结果不同
    
    print("✓ 一次一密测试通过")

def test_replay_detection():
    """测试重放攻击检测"""
    print("测试6: 重放攻击检测...")
    encoder = create_encoder("test_secret", "ua_001")
    
    # 编码一条消息
    encoded = encoder.encode_secure_message("Original message")
    
    # 第一次解码应该成功
    decoded1, verified1, msg_type1 = encoder.decode_secure_message(encoded)
    assert verified1 == True
    assert decoded1 == "Original message"
    
    # 第二次解码相同的消息应该检测到重复
    decoded2, verified2, msg_type2 = encoder.decode_secure_message(encoded)
    assert verified2 == False
    assert "重复" in decoded2 or "警告" in decoded2
    
    print("✓ 重放攻击检测测试通过")

def test_hmac_verification():
    """测试HMAC验证（防篡改）"""
    print("测试7: HMAC验证（防篡改）...")
    encoder = create_encoder("test_secret", "ua_001")
    
    # 编码一条消息
    encoded = encoder.encode_secure_message("Original message")
    
    # 修改内容（模拟篡改）
    encoded_tampered = encoded.copy()
    encoded_tampered['content'] = encoded['content'][:-1] + 'X'  # 修改最后一个字符
    
    # 尝试解码被篡改的消息
    decoded, verified, msg_type = encoder.decode_secure_message(encoded_tampered)
    assert verified == False
    assert "失败" in decoded or "错误" in decoded
    
    print("✓ HMAC验证测试通过")

def test_wrong_key():
    """测试错误密钥检测"""
    print("测试8: 错误密钥检测...")
    encoder_a = create_encoder("secret_key_A", "ua_001")
    encoder_b = create_encoder("secret_key_B", "ua_001")
    
    # A编码
    encoded = encoder_a.encode_secure_message("Secret")
    
    # B用错误的密钥解码（即使UA身份相同）
    decoded, verified, msg_type = encoder_b.decode_secure_message(encoded)
    assert verified == False
    
    print("✓ 错误密钥检测测试通过")

def test_sequence_persistence():
    """测试序列号持久化"""
    print("测试9: 序列号持久化...")
    encoder = create_encoder("test_secret", "ua_001")
    
    # 发送几封邮件
    encoder.encode_secure_message("Message 1")
    encoder.encode_secure_message("Message 2")
    encoder.encode_secure_message("Message 3")
    
    # 保存序列号
    config = encoder.to_dict()
    assert config['sent_sequence'] == 3
    
    # 从配置恢复
    encoder2 = create_encoder("test_secret", "ua_001")
    encoder2.sent_sequence = config['sent_sequence']
    
    # 下一封邮件应该使用序列号4
    encoded = encoder2.encode_secure_message("Message 4")
    assert encoded['sequence'] == 4
    
    print("✓ 序列号持久化测试通过")

def test_normal_message():
    """测试未加密消息处理"""
    print("测试10: 未加密消息处理...")
    encoder = create_encoder()  # 不提供密钥
    
    # 编码应该返回非安全模式
    encoded = encoder.encode_secure_message("Normal message")
    assert encoded['secure'] == False
    assert encoded['content'] == "Normal message"
    
    # 解码也应该直接返回
    decoded, verified, msg_type = encoder.decode_secure_message(encoded)
    assert decoded == "Normal message"
    assert verified == True
    assert msg_type == "normal"
    
    print("✓ 未加密消息处理测试通过")

def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始运行单元测试...")
    print("=" * 60)
    
    try:
        test_basic_encoding()
        test_chinese_encoding()
        test_attachment_encoding()
        test_ua_identity()
        test_one_time_pad()
        test_replay_detection()
        test_hmac_verification()
        test_wrong_key()
        test_sequence_persistence()
        test_normal_message()
        
        print("=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ 测试出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
