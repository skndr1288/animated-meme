#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أداة اختبار بطاقات البريبيد - النسخة المتقدمة مع تكامل تليجرام
Advanced Prepaid Card Testing Tool v3.0 with Telegram Integration
"""

import re
import json
import csv
import requests
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, List
from pathlib import Path
import hashlib
from enum import Enum
import threading
import time


class CardStatus(Enum):
    """حالات البطاقة"""
    VALID = "✅ صالحة"
    INVALID = "❌ غير صالحة"
    EXPIRED = "⏰ منتهية الصلاحية"
    SUSPICIOUS = "⚠️ مريبة"


class TransactionType(Enum):
    """أنواع المعاملات"""
    PURCHASE = "شراء"
    WITHDRAWAL = "سحب"
    TRANSFER = "تحويل"
    DEPOSIT = "إيداع"


class TelegramBot:
    """فئة للتعامل مع تليجرام"""
    
    def __init__(self, token: str, chat_id: str):
        """
        تهيئة بوت التليجرام
        
        Args:
            token: توكن البوت من BotFather
            chat_id: معرّف الدردشة
        """
        self.token = token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.is_connected = False
        self.test_connection()
    
    def test_connection(self) -> bool:
        """اختبار الاتصال بتليجرام"""
        try:
            response = requests.get(
                f"{self.api_url}/getMe",
                timeout=5
            )
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok'):
                    self.is_connected = True
                    print(f"✅ متصل بتليجرام: @{bot_info['result'].get('username')}")
                    return True
        except Exception as e:
            print(f"❌ خطأ في الاتصال بتليجرام: {e}")
        
        self.is_connected = False
        return False
    
    def send_message(self, text: str, parse_mode: str = 'HTML') -> bool:
        """
        إرسال رسالة إلى التليجرام
        
        Args:
            text: نص الرسالة
            parse_mode: نمط التنسيق (HTML/Markdown)
            
        Returns:
            نجاح الإرسال
        """
        if not self.is_connected:
            return False
        
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    'chat_id': self.chat_id,
                    'text': text,
                    'parse_mode': parse_mode
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ خطأ في الإرسال: {e}")
            return False
    
    def send_document(self, file_path: str, caption: str = '') -> bool:
        """
        إرسال ملف إلى التليجرام
        
        Args:
            file_path: مسار الملف
            caption: عنوان الملف
            
        Returns:
            نجاح الإرسال
        """
        if not self.is_connected:
            return False
        
        try:
            with open(file_path, 'rb') as f:
                response = requests.post(
                    f"{self.api_url}/sendDocument",
                    data={
                        'chat_id': self.chat_id,
                        'caption': caption
                    },
                    files={'document': f},
                    timeout=30
                )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ خطأ في إرسال الملف: {e}")
            return False
    
    def send_card_alert(self, card_info: Dict, status: str):
        """إرسال تنبيه اختبار البطاقة"""
        message = f"""
<b>🔔 تنبيه اختبار بطاقة</b>

<b>النوع:</b> {card_info.get('card_type')}
<b>آخر 4 أرقام:</b> {card_info.get('card_number')}
<b>الحامل:</b> {card_info.get('holder')}
<b>المبلغ:</b> ${card_info.get('amount', 0):.2f}

<b>الحالة:</b> {status}
<b>التقييم:</b> {card_info.get('overall_rating', 0):.1f}/10

<i>الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
"""
        self.send_message(message)
    
    def send_statistics(self, stats: Dict):
        """إرسال الإحصائيات"""
        message = f"""
<b>📊 إحصائيات الاختبارات</b>

<b>إجمالي الاختبارات:</b> {stats.get('إجمالي_الاختبارات')}
<b>البطاقات الصحيحة:</b> {stats.get('البطاقات_الصحيحة')}
<b>معدل النجاح:</b> {stats.get('معدل_النجاح')}
<b>متوسط التقييم:</b> {stats.get('متوسط_التقييم')}

<b>إجمالي المعاملات:</b> {stats.get('إجمالي_المعاملات')}
<b>المعاملات الناجحة:</b> {stats.get('المعاملات_الناجحة')}
<b>إجمالي المبلغ:</b> {stats.get('إجمالي_المبلغ')}

<i>الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
"""
        self.send_message(message)


class PrepaidCardTester:
    """فئة متقدمة لاختبار بطاقات البريبيد مع تكامل تليجرام"""
    
    TEST_CARDS = {
        'visa': {
            'number': '4532015112830366',
            'cvv': '123',
            'expiry': '12/25',
            'holder': 'Test User',
            'type': 'Visa',
            'balance': 5000.00,
            'daily_limit': 1000.00
        },
        'mastercard': {
            'number': '5425233010103442',
            'cvv': '456',
            'expiry': '11/26',
            'holder': 'Test User',
            'type': 'Mastercard',
            'balance': 10000.00,
            'daily_limit': 2000.00
        },
        'amex': {
            'number': '378282246310005',
            'cvv': '7890',
            'expiry': '10/24',
            'holder': 'Test User',
            'type': 'American Express',
            'balance': 15000.00,
            'daily_limit': 3000.00
        },
        'discover': {
            'number': '6011111111111117',
            'cvv': '234',
            'expiry': '09/27',
            'holder': 'Test User',
            'type': 'Discover',
            'balance': 8000.00,
            'daily_limit': 1500.00
        }
    }
    
    def __init__(self, storage_file: str = 'card_test_results.json', 
                 telegram_token: str = None, telegram_chat_id: str = None):
        """تهيئة الأداة مع تكامل تليجرام"""
        self.results = []
        self.transactions = []
        self.storage_file = storage_file
        self.cards_database = {}
        
        # تكامل تليجرام
        self.telegram = None
        if telegram_token and telegram_chat_id:
            self.telegram = TelegramBot(telegram_token, telegram_chat_id)
        
        self.load_results()
    
    def log_to_telegram(self, message: str):
        """تسجيل رسالة في تليجرام"""
        if self.telegram and self.telegram.is_connected:
            self.telegram.send_message(message)
    
    def save_results(self):
        """حفظ النتائج في ملف JSON"""
        data = {
            'results': self.results,
            'transactions': self.transactions,
            'saved_at': datetime.now().isoformat()
        }
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ تم حفظ النتائج في {self.storage_file}")
            
            # إرسال تنبيه تليجرام
            self.log_to_telegram(f"💾 تم حفظ النتائج - {len(self.results)} اختبار")
        except Exception as e:
            print(f"❌ خطأ في حفظ النتائج: {e}")
    
    def load_results(self):
        """تحميل النتائج من ملف JSON"""
        try:
            if Path(self.storage_file).exists():
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.results = data.get('results', [])
                    self.transactions = data.get('transactions', [])
                    print(f"✅ تم تحميل {len(self.results)} نتيجة اختبار")
        except Exception as e:
            print(f"⚠️ لم يتمكن من تحميل النتائج: {e}")
    
    def export_to_csv(self, filename: str = 'card_test_results.csv'):
        """تصدير النتائج إلى ملف CSV"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                if self.results:
                    writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
                    writer.writeheader()
                    writer.writerows(self.results)
                    print(f"✅ تم تصدير النتائج إلى {filename}")
                    
                    # إرسال الملف إلى تليجرام
                    if self.telegram and self.telegram.is_connected:
                        self.telegram.send_document(
                            filename,
                            f"📊 نتائج الاختبارات - {len(self.results)} بطاقة"
                        )
        except Exception as e:
            print(f"❌ خطأ في التصدير: {e}")
    
    def validate_card_number(self, card_number: str) -> Tuple[bool, str]:
        """التحقق من رقم البطاقة باستخدام خوارزمية Luhn"""
        card_number = card_number.replace(' ', '').replace('-', '')
        
        if not card_number.isdigit():
            return False, "❌ رقم البطاقة يجب أن يحتوي على أرقام فقط"
        
        if len(card_number) < 13 or len(card_number) > 19:
            return False, "❌ طول رقم البطاقة غير صحيح (13-19 رقم)"
        
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
        """التحقق من رمز CVV مع دعم أنواع مختلفة"""
        if card_type.lower() == 'amex':
            expected_length = 4
        else:
            expected_length = 3
        
        if not cvv.isdigit():
            return False, "❌ CVV يجب أن يحتوي على أرقام فقط"
        
        if len(cvv) != expected_length:
            return False, f"❌ CVV يجب أن يكون {expected_length} أرقام"
        
        return True, f"✅ CVV صحيح ({expected_length} أرقام)"
    
    def validate_expiry(self, expiry: str) -> Tuple[bool, str, Optional[datetime]]:
        """التحقق من تاريخ انتهاء الصلاحية"""
        if '/' not in expiry:
            return False, "❌ صيغة التاريخ يجب أن تكون MM/YY", None
        
        try:
            month, year = expiry.split('/')
            month = int(month)
            year = int(year)
            
            if month < 1 or month > 12:
                return False, "❌ الشهر يجب أن يكون بين 1-12", None
            
            current_year = datetime.now().year
            if year < 100:
                year += 2000
            
            expiry_date = datetime(year, month, 1) + timedelta(days=32)
            
            if datetime.now() > expiry_date:
                return False, "❌ البطاقة منتهية الصلاحية", expiry_date
            
            days_remaining = (expiry_date - datetime.now()).days
            return True, f"✅ البطاقة صالحة حتى {month:02d}/{year % 100:02d} ({days_remaining} يوم)", expiry_date
        
        except ValueError:
            return False, "❌ صيغة التاريخ غير صحيحة", None
    
    def validate_holder_name(self, holder: str) -> Tuple[bool, str]:
        """التحقق من اسم حامل البطاقة"""
        if not holder or len(holder) < 3:
            return False, "❌ اسم حامل البطاقة يجب أن يكون 3 أحرف على الأقل"
        
        if len(holder) > 50:
            return False, "❌ اسم حامل البطاقة طويل جداً"
        
        return True, f"✅ اسم حامل البطاقة صحيح: {holder}"
    
    def detect_card_type(self, card_number: str) -> str:
        """تحديد نوع البطاقة"""
        card_number = card_number.replace(' ', '').replace('-', '')
        
        patterns = {
            'Visa': r'^4[0-9]{12}(?:[0-9]{3})?$',
            'Mastercard': r'^5[1-5][0-9]{14}$',
            'American Express': r'^3[47][0-9]{13}$',
            'Discover': r'^6(?:011|5[0-9]{2})[0-9]{12}$',
            'Diners Club': r'^3(?:0[0-5]|[68][0-9])[0-9]{11}$',
            'JCB': r'^(?:2131|1800|35\d{3})\d{11}$'
        }
        
        for card_type, pattern in patterns.items():
            if re.match(pattern, card_number):
                return card_type
        
        return 'Unknown'
    
    def calculate_card_hash(self, card_number: str) -> str:
        """حساب بصمة البطاقة (Hash) للأمان"""
        return hashlib.sha256(card_number.encode()).hexdigest()[:16]
    
    def check_card_risk(self, card_number: str, amount: float, 
                       daily_limit: float, used_today: float) -> Tuple[str, str]:
        """فحص المخاطر المحتملة"""
        risks = []
        
        if amount > daily_limit:
            risks.append("المبلغ يتجاوز الحد اليومي")
        
        if used_today + amount > daily_limit:
            risks.append("تجاوز الحد اليومي بعد هذه المعاملة")
        
        if amount > 5000:
            risks.append("مبلغ كبير جداً")
        
        if len(risks) == 0:
            return CardStatus.VALID.value, "آمن"
        elif len(risks) <= 2:
            return CardStatus.SUSPICIOUS.value, ", ".join(risks)
        else:
            return CardStatus.INVALID.value, ", ".join(risks)
    
    def test_card(self, card_number: str, cvv: str, expiry: str, 
                  holder: str = 'Test User', amount: float = 100.0) -> Dict:
        """اختبار البطاقة بشكل شامل"""
        card_type = self.detect_card_type(card_number)
        card_hash = self.calculate_card_hash(card_number)
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'card_hash': card_hash,
            'card_number': card_number[-4:],
            'card_type': card_type,
            'holder': holder,
            'amount': amount,
            'tests': {},
            'details': {}
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
        is_valid, message, expiry_date = self.validate_expiry(expiry)
        result['tests']['تاريخ_الانتهاء'] = message
        result['expiry_valid'] = is_valid
        result['details']['expiry_date'] = expiry_date.isoformat() if expiry_date else None
        
        # اختبار اسم حامل البطاقة
        is_valid, message = self.validate_holder_name(holder)
        result['tests']['اسم_الحامل'] = message
        result['holder_valid'] = is_valid
        
        # فحص المخاطر
        status, risk_message = self.check_card_risk(
            card_number, amount, 1000.0, 0.0
        )
        result['tests']['فحص_المخاطر'] = f"{status} - {risk_message}"
        result['risk_status'] = status
        
        # الحالة النهائية
        all_valid = all([
            result['card_valid'],
            result['cvv_valid'],
            result['expiry_valid'],
            result['holder_valid']
        ])
        
        result['status'] = CardStatus.VALID.value if all_valid else CardStatus.INVALID.value
        result['overall_rating'] = self.calculate_rating(result)
        
        self.results.append(result)
        
        # إرسال تنبيه تليجرام
        if self.telegram and self.telegram.is_connected:
            self.telegram.send_card_alert(result, result['status'])
        
        return result
    
    def calculate_rating(self, result: Dict) -> float:
        """حساب تقييم البطاقة من 1-10"""
        score = 0
        if result['card_valid']:
            score += 3
        if result['cvv_valid']:
            score += 2
        if result['expiry_valid']:
            score += 2
        if result['holder_valid']:
            score += 2
        if CardStatus.VALID.value in result['tests']['فحص_المخاطر']:
            score += 1
        
        return min(10, score)
    
    def simulate_transaction(self, card_number: str, amount: float, 
                            trans_type: TransactionType) -> Dict:
        """محاكاة معاملة مالية"""
        transaction = {
            'timestamp': datetime.now().isoformat(),
            'card_hash': self.calculate_card_hash(card_number),
            'amount': amount,
            'type': trans_type.value,
            'status': 'معالجة...'
        }
        
        is_valid, _ = self.validate_card_number(card_number)
        transaction['status'] = '✅ تمت بنجاح' if is_valid else '❌ فشلت'
        
        self.transactions.append(transaction)
        
        # إرسال تنبيه تليجرام
        if self.telegram and self.telegram.is_connected:
            self.log_to_telegram(
                f"💰 معاملة {trans_type.value}: ${amount:.2f} - {transaction['status']}"
            )
        
        return transaction
    
    def get_statistics(self) -> Dict:
        """الحصول على إحصائيات الاختبارات"""
        total_tests = len(self.results)
        valid_cards = sum(1 for r in self.results if r['card_valid'])
        avg_rating = sum(r.get('overall_rating', 0) for r in self.results) / max(1, total_tests)
        
        total_amount = sum(t.get('amount', 0) for t in self.transactions)
        successful_trans = sum(1 for t in self.transactions if '✅' in t.get('status', ''))
        
        return {
            'إجمالي_الاختبارات': total_tests,
            'البطاقات_الصحيحة': valid_cards,
            'معدل_النجاح': f"{(valid_cards/max(1, total_tests)*100):.2f}%",
            'متوسط_التقييم': f"{avg_rating:.2f}/10",
            'إجمالي_المعاملات': len(self.transactions),
            'المعاملات_الناجحة': successful_trans,
            'إجمالي_المبلغ': f"${total_amount:,.2f}"
        }
    
    def print_result(self, result: Dict):
        """طباعة نتائج الاختبار بشكل جميل"""
        print("\n" + "="*60)
        print("📊 نتيجة اختبار البطاقة")
        print("="*60)
        print(f"الوقت: {result['timestamp']}")
        print(f"نوع البطاقة: {result['card_type']}")
        print(f"آخر 4 أرقام: {result['card_number']}")
        print(f"حامل البطاقة: {result['holder']}")
        print(f"المبلغ المختبر: ${result['amount']:.2f}")
        print(f"بصمة البطاقة: {result['card_hash']}")
        
        print(f"\n📋 نتائج الاختبارات:")
        for test_name, message in result['tests'].items():
            print(f"  {test_name}: {message}")
        
        print(f"\n📈 التقييم: {result['overall_rating']:.1f}/10")
        print(f"الحالة النهائية: {result['status']}")
        print("="*60 + "\n")
    
    def display_test_cards(self):
        """عرض بطاقات الاختبار المتاحة"""
        print("\n" + "="*60)
        print("💳 بطاقات الاختبار المتاحة")
        print("="*60)
        for i, (card_type, details) in enumerate(self.TEST_CARDS.items(), 1):
            print(f"\n{i}. {details['type'].upper()}")
            print(f"   الرقم: {details['number']}")
            print(f"   CVV: {details['cvv']}")
            print(f"   الانتهاء: {details['expiry']}")
            print(f"   الحامل: {details['holder']}")
            print(f"   الرصيد: ${details['balance']:,.2f}")
            print(f"   الحد اليومي: ${details['daily_limit']:,.2f}")
        print("="*60 + "\n")
    
    def display_statistics(self):
        """عرض الإحصائيات"""
        stats = self.get_statistics()
        print("\n" + "="*60)
        print("📊 الإحصائيات الإجمالية")
        print("="*60)
        for key, value in stats.items():
            print(f"{key}: {value}")
        print("="*60 + "\n")
        
        # إرسال الإحصائيات إلى تليجرام
        if self.telegram and self.telegram.is_connected:
            self.telegram.send_statistics(stats)


def get_telegram_credentials():
    """الحصول على بيانات تليجرام من المستخدم"""
    print("\n" + "="*60)
    print("🤖 إعدادات التكامل مع تليجرام")
    print("="*60)
    print("\nهل تريد تفعيل تكامل تليجرام؟")
    print("1. نعم")
    print("2. لا")
    
    choice = input("اختر (1/2): ").strip()
    
    if choice == '1':
        print("\n📋 تعليمات الحصول على بيانات تليجرام:")
        print("1. اذهب إلى @BotFather على تليجرام")
        print("2. أرسل: /newbot")
        print("3. اتبع التعليمات واحصل على التوكن")
        print("4. اذهب إلى @userinfobot واحصل على Chat ID")
        
        token = input("\nأدخل توكن البوت: ").strip()
        chat_id = input("أدخل Chat ID: ").strip()
        
        if token and chat_id:
            return token, chat_id
    
    return None, None


def main():
    """الدالة الرئيسية مع واجهة تفاعلية محسنة"""
    
    print("\n" + "🎯 "*15)
    print("أداة اختبار بطاقات البريبيد - النسخة المتقدمة v3.0")
    print("مع تكامل تليجرام الكامل")
    print("Advanced Prepaid Card Testing Tool v3.0 with Telegram")
    print("🎯 "*15)
    
    # الحصول على بيانات تليجرام
    telegram_token, telegram_chat_id = get_telegram_credentials()
    
    # إنشاء الأداة
    tester = PrepaidCardTester(
        telegram_token=telegram_token,
        telegram_chat_id=telegram_chat_id
    )
    
    if telegram_token and telegram_chat_id:
        tester.log_to_telegram("🚀 تم بدء أداة اختبار البطاقات")
    
    while True:
        print("\n" + "-"*60)
        print("القائمة الرئيسية:")
        print("-"*60)
        print("1. عرض بطاقات الاختبار")
        print("2. اختبار بطاقة العينات")
        print("3. اختبار بطاقة يدوية")
        print("4. محاكاة معاملة مالية")
        print("5. عرض الإحصائيات")
        print("6. تصدير النتائج إلى CSV")
        print("7. حفظ النتائج")
        print("8. خروج")
        print("-"*60)
        
        choice = input("اختر الخيار (1-8): ").strip()
        
        if choice == '1':
            tester.display_test_cards()
        
        elif choice == '2':
            print("\n🧪 اختبار بطاقات العينات...")
            tester.log_to_telegram("🧪 بدء اختبار بطاقات العينات...")
            
            for card_type, card_data in tester.TEST_CARDS.items():
                result = tester.test_card(
                    card_number=card_data['number'],
                    cvv=card_data['cvv'],
                    expiry=card_data['expiry'],
                    holder=card_data['holder'],
                    amount=500.00
                )
                tester.print_result(result)
        
        elif choice == '3':
            print("\n✍️ اختبار يدوي")
            try:
                card_num = input("أدخل رقم البطاقة: ").strip()
                if not card_num:
                    continue
                
                cvv = input("أدخل CVV: ").strip()
                expiry = input("أدخل تاريخ الانتهاء (MM/YY): ").strip()
                holder = input("أدخل اسم حامل البطاقة: ").strip() or "Test User"
                amount = float(input("أدخل المبلغ ($): ").strip() or "100")
                
                result = tester.test_card(card_num, cvv, expiry, holder, amount)
                tester.print_result(result)
            
            except ValueError:
                print("❌ إدخال غير صحيح")
                tester.log_to_telegram("❌ خطأ: إدخال غير صحيح في الاختبار اليدوي")
            except Exception as e:
                print(f"❌ خطأ: {e}")
                tester.log_to_telegram(f"❌ خطأ: {e}")
        
        elif choice == '4':
            print("\n💰 محاكاة معاملة مالية")
            try:
                card_num = input("أدخل رقم البطاقة: ").strip()
                amount = float(input("أدخل المبلغ ($): ").strip() or "100")
                
                print("نوع المعاملة:")
                for i, trans_type in enumerate(TransactionType, 1):
                    print(f"{i}. {trans_type.value}")
                
                trans_choice = int(input("اختر نوع المعاملة: ").strip() or "1") - 1
                trans_type = list(TransactionType)[trans_choice]
                
                trans = tester.simulate_transaction(card_num, amount, trans_type)
                print(f"\n✅ المعاملة: {trans['type']} - {trans['status']}")
            
            except Exception as e:
                print(f"❌ خطأ: {e}")
                tester.log_to_telegram(f"❌ خطأ في المعاملة: {e}")
        
        elif choice == '5':
            tester.display_statistics()
        
        elif choice == '6':
            tester.export_to_csv()
        
        elif choice == '7':
            tester.save_results()
        
        elif choice == '8':
            print("\n👋 شكراً لاستخدام الأداة!")
            if tester.telegram and tester.telegram.is_connected:
                tester.log_to_telegram("👋 تم إيقاف أداة الاختبار")
            break
        
        else:
            print("❌ اختيار غير صحيح")


if __name__ == '__main__':
    main()
