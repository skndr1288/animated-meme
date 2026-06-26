#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أداة اختبار بطاقات البريبيد
Prepaid Card Testing Tool
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional


class PrepaidCardTester:
    """فئة لاختبار بطاقات البريبيد"""
    
    # بطاقات اختبار وهمية
    TEST_CARDS = {
        'visa': {
            'number': '4532015112830366',
            'cvv': '123',
            'expiry': '12/25',
            'holder': 'Test User',
            'type': 'Visa'
        },
        'mastercard': {
            'number': '5425233010103442',
            'cvv': '456',
            'expiry': '11/26',
            'holder': 'Test User',
            'type': 'Mastercard'
        },
        'amex': {
            'number': '378282246310005',
            'cvv': '7890',
            'expiry': '10/24',
            'holder': 'Test User',
            'type': 'American Express'
        }
    }
    
    def __init__(self):
        """تهيئة الأداة"""
        self.results = []
    
    def validate_card_number(self, card_number: str) -> Tuple[bool, str]:
        """
        التحقق من رقم البطاقة باستخدام خوارزمية Luhn
        
        Args:
            card_number: رقم البطاقة
            
        Returns:
            (صحيح/خاطئ، الرسالة)
        """
        # إزالة المسافات والشرطات
        card_number = card_number.replace(' ', '').replace('-', '')
        
        # التحقق من أن الرقم يحتوي على أرقام فقط
        if not card_number.isdigit():
            return False, "❌ رقم البطاقة يجب أن يحتوي على أرقام فقط"
        
        # التحقق من الطول
        if len(card_number) < 13 or len(card_number) > 19:
            return False, "❌ طول رقم البطاقة غير صحيح (13-19 رقم)"
        
        # خوارزمية Luhn
        def luhn_checksum(num):
            def digits_of(n):
                return [int(d) for d in str(n)]
            
            digits = digits_of(num)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d * 2))
            
            return checksum % 10
        
        if luhn_checksum(card_number) != 0:
            return False, "❌ رقم البطاقة غير صحيح (فشل اختبار Luhn)"
        
        return True, "✅ رقم البطاقة صحيح"
    
    def validate_cvv(self, cvv: str, card_type: str = 'visa') -> Tuple[bool, str]:
        """
        التحقق من رمز CVV
        
        Args:
            cvv: رمز الأمان
            card_type: نوع البطاقة
            
        Returns:
            (صحيح/خاطئ، الرسالة)
        """
        # Amex يحتاج 4 أرقام، البقية تحتاج 3
        if card_type.lower() == 'amex':
            expected_length = 4
        else:
            expected_length = 3
        
        if not cvv.isdigit():
            return False, "❌ CVV يجب أن يحتوي على أرقام فقط"
        
        if len(cvv) != expected_length:
            return False, f"❌ CVV يجب أن يكون {expected_length} أرقام"
        
        return True, f"✅ CVV صحيح ({expected_length} أرقام)"
    
    def validate_expiry(self, expiry: str) -> Tuple[bool, str]:
        """
        التحقق من تاريخ انتهاء الصلاحية
        
        Args:
            expiry: تاريخ الانتهاء (MM/YY)
            
        Returns:
            (صحيح/خاطئ، الرسالة)
        """
        if '/' not in expiry:
            return False, "❌ صيغة التاريخ يجب أن تكون MM/YY"
        
        try:
            month, year = expiry.split('/')
            month = int(month)
            year = int(year)
            
            if month < 1 or month > 12:
                return False, "❌ الشهر يجب أن يكون بين 1-12"
            
            # تحويل السنة إلى سنة كاملة
            current_year = datetime.now().year
            if year < 100:
                year += 2000
            
            # التحقق من عدم انتهاء الصلاحية
            expiry_date = datetime(year, month, 1) + timedelta(days=32)
            if datetime.now() > expiry_date:
                return False, "❌ البطاقة منتهية الصلاحية"
            
            return True, f"✅ البطاقة صالحة حتى {month:02d}/{year % 100:02d}"
        
        except ValueError:
            return False, "❌ صيغة التاريخ غير صحيحة"
    
    def detect_card_type(self, card_number: str) -> str:
        """
        تحديد نوع البطاقة
        
        Args:
            card_number: رقم البطاقة
            
        Returns:
            نوع البطاقة
        """
        card_number = card_number.replace(' ', '').replace('-', '')
        
        if card_number.startswith('4'):
            return 'Visa'
        elif card_number.startswith('5'):
            return 'Mastercard'
        elif card_number.startswith('3'):
            return 'American Express'
        elif card_number.startswith('6'):
            return 'Discover'
        else:
            return 'Unknown'
    
    def test_card(self, card_number: str, cvv: str, expiry: str, 
                  holder: str = 'Test User') -> Dict:
        """
        اختبار البطاقة بشكل كامل
        
        Args:
            card_number: رقم البطاقة
            cvv: رمز الأمان
            expiry: تاريخ الانتهاء
            holder: اسم حامل البطاقة
            
        Returns:
            قاموس بنتائج الاختبار
        """
        card_type = self.detect_card_type(card_number)
        
        result = {
            'card_number': card_number[-4:],  # آخر 4 أرقام فقط
            'card_type': card_type,
            'holder': holder,
            'tests': {}
        }
        
        # اختبار رقم البطاقة
        is_valid, message = self.validate_card_number(card_number)
        result['tests']['رقم_البطاقة'] = message
        result['card_valid'] = is_valid
        
        # اختبار CVV
        is_valid, message = self.validate_cvv(cvv, card_type)
        result['tests']['CVV'] = message
        result['cvv_valid'] = is_valid
        
        # اختبار الانتهاء
        is_valid, message = self.validate_expiry(expiry)
        result['tests']['تاريخ_الانتهاء'] = message
        result['expiry_valid'] = is_valid
        
        # الحالة النهائية
        result['status'] = '✅ البطاقة صالحة' if all([
            result['card_valid'],
            result['cvv_valid'],
            result['expiry_valid']
        ]) else '❌ البطاقة غير صالحة'
        
        self.results.append(result)
        return result
    
    def print_result(self, result: Dict):
        """طباعة نتائج الاختبار"""
        print("\n" + "="*50)
        print(f"نتيجة اختبار البطاقة")
        print("="*50)
        print(f"نوع البطاقة: {result['card_type']}")
        print(f"آخر 4 أرقام: {result['card_number']}")
        print(f"حامل البطاقة: {result['holder']}")
        print(f"\nنتائج الاختبارات:")
        for test_name, message in result['tests'].items():
            print(f"  {test_name}: {message}")
        print(f"\n{result['status']}")
        print("="*50)
    
    def display_test_cards(self):
        """عرض بطاقات الاختبار المتاحة"""
        print("\n" + "="*50)
        print("بطاقات الاختبار المتاحة")
        print("="*50)
        for card_type, details in self.TEST_CARDS.items():
            print(f"\n{card_type.upper()}:")
            print(f"  الرقم: {details['number']}")
            print(f"  CVV: {details['cvv']}")
            print(f"  الانتهاء: {details['expiry']}")
            print(f"  الحامل: {details['holder']}")
        print("="*50 + "\n")


def main():
    """الدالة الرئيسية"""
    tester = PrepaidCardTester()
    
    print("\n" + "🎯 "*10)
    print("مرحباً بك في أداة اختبار بطاقات البريبيد")
    print("Welcome to Prepaid Card Testing Tool")
    print("🎯 "*10 + "\n")
    
    # عرض بطاقات الاختبار
    tester.display_test_cards()
    
    # اختبار بطاقات العينة
    for card_type, card_data in tester.TEST_CARDS.items():
        print(f"\n🧪 اختبار بطاقة {card_data['type']}...")
        result = tester.test_card(
            card_number=card_data['number'],
            cvv=card_data['cvv'],
            expiry=card_data['expiry'],
            holder=card_data['holder']
        )
        tester.print_result(result)
    
    # اختبار يدوي
    print("\n" + "="*50)
    print("اختبار يدوي")
    print("="*50)
    
    try:
        card_num = input("\nأدخل رقم البطاقة (أو اضغط Enter للتخطي): ").strip()
        if card_num:
            cvv = input("أدخل CVV: ").strip()
            expiry = input("أدخل تاريخ الانتهاء (MM/YY): ").strip()
            holder = input("أدخل اسم حامل البطاقة: ").strip() or "Test User"
            
            result = tester.test_card(card_num, cvv, expiry, holder)
            tester.print_result(result)
    except KeyboardInterrupt:
        print("\n\nتم الإيقاف من قبل المستخدم")
    except Exception as e:
        print(f"\n❌ حدث خطأ: {e}")


if __name__ == '__main__':
    main()
