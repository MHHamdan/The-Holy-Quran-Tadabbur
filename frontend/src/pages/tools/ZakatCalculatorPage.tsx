/**
 * ZakatCalculatorPage - FANG-level production component
 *
 * Features:
 * - Real-time metal prices with caching
 * - Persistent state in localStorage
 * - Memoized calculations for performance
 * - Full accessibility (ARIA, keyboard navigation)
 * - Error boundaries and loading states
 */

import { memo, useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  Calculator,
  DollarSign,
  Coins,
  PiggyBank,
  Building2,
  CreditCard,
  TrendingUp,
  RefreshCw,
  Info,
  AlertCircle,
  CheckCircle,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  type LucideIcon,
} from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import {
  getMetalPrices,
  type MetalPrices,
} from '../../lib/islamicApis';
import { useAsync } from '../../hooks/useAsync';
import { useLocalStorage } from '../../hooks/useLocalStorage';
import { ErrorBoundary, InlineError } from '../../components/ui/ErrorBoundary';
import { Skeleton } from '../../components/ui/Skeleton';
import clsx from 'clsx';

// ============================================
// Types
// ============================================

interface Currency {
  code: string;
  symbol: string;
  name_en: string;
  name_ar: string;
  rate: number;
}

interface AssetField {
  id: string;
  name_en: string;
  name_ar: string;
  type: 'currency' | 'weight_gold' | 'weight_silver';
  hint_en?: string;
  hint_ar?: string;
}

interface AssetCategory {
  id: string;
  name_en: string;
  name_ar: string;
  icon: LucideIcon;
  color: string;
  fields: AssetField[];
}

interface ZakatResult {
  totalAssets: number;
  totalLiabilities: number;
  netWorth: number;
  zakatDue: number;
  meetsNisab: boolean;
  goldNisab: number;
  silverNisab: number;
}

// ============================================
// Constants
// ============================================

const ZAKAT_RATE = 0.025; // 2.5%
const GOLD_NISAB_GRAMS = 85;
const SILVER_NISAB_GRAMS = 595;

const CURRENCIES: Currency[] = [
  { code: 'USD', symbol: '$', name_en: 'US Dollar', name_ar: 'دولار أمريكي', rate: 1 },
  { code: 'EUR', symbol: '€', name_en: 'Euro', name_ar: 'يورو', rate: 0.92 },
  { code: 'GBP', symbol: '£', name_en: 'British Pound', name_ar: 'جنيه إسترليني', rate: 0.79 },
  { code: 'SAR', symbol: 'ر.س', name_en: 'Saudi Riyal', name_ar: 'ريال سعودي', rate: 3.75 },
  { code: 'AED', symbol: 'د.إ', name_en: 'UAE Dirham', name_ar: 'درهم إماراتي', rate: 3.67 },
  { code: 'EGP', symbol: 'ج.م', name_en: 'Egyptian Pound', name_ar: 'جنيه مصري', rate: 50.85 },
  { code: 'PKR', symbol: '₨', name_en: 'Pakistani Rupee', name_ar: 'روبية باكستانية', rate: 278 },
  { code: 'INR', symbol: '₹', name_en: 'Indian Rupee', name_ar: 'روبية هندية', rate: 83 },
  { code: 'MYR', symbol: 'RM', name_en: 'Malaysian Ringgit', name_ar: 'رينغيت ماليزي', rate: 4.47 },
  { code: 'IDR', symbol: 'Rp', name_en: 'Indonesian Rupiah', name_ar: 'روبية إندونيسية', rate: 15800 },
] as const;

const ASSET_CATEGORIES: AssetCategory[] = [
  {
    id: 'cash',
    name_en: 'Cash & Bank Balances',
    name_ar: 'النقود والأرصدة البنكية',
    icon: DollarSign,
    color: 'green',
    fields: [
      { id: 'cash_on_hand', name_en: 'Cash on Hand', name_ar: 'النقود في اليد', type: 'currency' },
      { id: 'bank_savings', name_en: 'Savings Accounts', name_ar: 'حسابات التوفير', type: 'currency' },
      { id: 'bank_checking', name_en: 'Checking Accounts', name_ar: 'الحسابات الجارية', type: 'currency' },
      { id: 'foreign_currency', name_en: 'Foreign Currency', name_ar: 'العملات الأجنبية', type: 'currency' },
    ],
  },
  {
    id: 'precious_metals',
    name_en: 'Gold & Silver',
    name_ar: 'الذهب والفضة',
    icon: Coins,
    color: 'amber',
    fields: [
      { id: 'gold_jewelry', name_en: 'Gold Jewelry (grams)', name_ar: 'مجوهرات الذهب (جرام)', type: 'weight_gold', hint_en: 'Include all gold jewelry', hint_ar: 'اشمل جميع مجوهرات الذهب' },
      { id: 'gold_coins', name_en: 'Gold Coins/Bars (grams)', name_ar: 'عملات/سبائك الذهب (جرام)', type: 'weight_gold' },
      { id: 'silver_items', name_en: 'Silver Items (grams)', name_ar: 'الفضة (جرام)', type: 'weight_silver' },
    ],
  },
  {
    id: 'investments',
    name_en: 'Investments',
    name_ar: 'الاستثمارات',
    icon: TrendingUp,
    color: 'blue',
    fields: [
      { id: 'stocks', name_en: 'Stocks & Shares', name_ar: 'الأسهم', type: 'currency', hint_en: 'Current market value', hint_ar: 'القيمة السوقية الحالية' },
      { id: 'mutual_funds', name_en: 'Mutual Funds', name_ar: 'صناديق الاستثمار', type: 'currency' },
      { id: 'retirement', name_en: 'Retirement Accounts', name_ar: 'حسابات التقاعد', type: 'currency', hint_en: 'Only if accessible', hint_ar: 'فقط إذا كان يمكن الوصول إليها' },
      { id: 'crypto', name_en: 'Cryptocurrency', name_ar: 'العملات الرقمية', type: 'currency' },
    ],
  },
  {
    id: 'business',
    name_en: 'Business Assets',
    name_ar: 'أصول الأعمال',
    icon: Building2,
    color: 'purple',
    fields: [
      { id: 'inventory', name_en: 'Inventory/Stock', name_ar: 'المخزون', type: 'currency' },
      { id: 'receivables', name_en: 'Accounts Receivable', name_ar: 'المستحقات', type: 'currency', hint_en: 'Expected to be collected', hint_ar: 'المتوقع تحصيلها' },
      { id: 'cash_business', name_en: 'Business Cash', name_ar: 'النقد التجاري', type: 'currency' },
    ],
  },
  {
    id: 'debts_owed',
    name_en: 'Money Owed to You',
    name_ar: 'الأموال المستحقة لك',
    icon: PiggyBank,
    color: 'teal',
    fields: [
      { id: 'loans_given', name_en: 'Loans Given', name_ar: 'القروض الممنوحة', type: 'currency', hint_en: 'Expected to be repaid', hint_ar: 'المتوقع سدادها' },
      { id: 'deposits', name_en: 'Security Deposits', name_ar: 'الودائع الضمانية', type: 'currency' },
    ],
  },
  {
    id: 'liabilities',
    name_en: 'Deductible Liabilities',
    name_ar: 'الالتزامات المخصومة',
    icon: CreditCard,
    color: 'red',
    fields: [
      { id: 'debts_immediate', name_en: 'Immediate Debts', name_ar: 'الديون الفورية', type: 'currency', hint_en: 'Due within the year', hint_ar: 'المستحقة خلال السنة' },
      { id: 'bills_due', name_en: 'Bills & Expenses Due', name_ar: 'الفواتير والمصاريف المستحقة', type: 'currency' },
      { id: 'taxes_due', name_en: 'Taxes Due', name_ar: 'الضرائب المستحقة', type: 'currency' },
    ],
  },
] as const;

const ZAKAT_RECIPIENTS = [
  { id: 'fuqara', name_en: 'The Poor (Fuqara)', name_ar: 'الفقراء' },
  { id: 'masakin', name_en: 'The Needy (Masakin)', name_ar: 'المساكين' },
  { id: 'amilin', name_en: 'Zakat Collectors', name_ar: 'العاملين عليها' },
  { id: 'muallafat', name_en: 'New Muslims', name_ar: 'المؤلفة قلوبهم' },
  { id: 'riqab', name_en: 'Freeing Captives', name_ar: 'في الرقاب' },
  { id: 'gharimin', name_en: 'Debtors', name_ar: 'الغارمين' },
  { id: 'fisabilillah', name_en: "In Allah's Cause", name_ar: 'في سبيل الله' },
  { id: 'ibnsabil', name_en: 'Travelers', name_ar: 'ابن السبيل' },
] as const;

const COLOR_CLASSES: Record<string, { bg: string; text: string; border: string }> = {
  green: { bg: 'bg-green-100', text: 'text-green-600', border: 'border-green-300' },
  amber: { bg: 'bg-amber-100', text: 'text-amber-600', border: 'border-amber-300' },
  blue: { bg: 'bg-blue-100', text: 'text-blue-600', border: 'border-blue-300' },
  purple: { bg: 'bg-purple-100', text: 'text-purple-600', border: 'border-purple-300' },
  teal: { bg: 'bg-teal-100', text: 'text-teal-600', border: 'border-teal-300' },
  red: { bg: 'bg-red-100', text: 'text-red-600', border: 'border-red-300' },
};

// ============================================
// Custom Hook: useMetalPrices
// ============================================

function useMetalPrices() {
  const fetchPrices = useCallback(() => getMetalPrices(), []);
  const { execute, isPending, isError, data, error } = useAsync(fetchPrices, {
    retryCount: 2,
  });

  useEffect(() => {
    execute();
  }, [execute]);

  return {
    prices: data,
    loading: isPending,
    error: isError ? error : null,
    refetch: execute,
  };
}

// ============================================
// Custom Hook: useZakatCalculation
// ============================================

function useZakatCalculation(
  assets: Record<string, number>,
  metalPrices: MetalPrices | null,
  currency: Currency
): ZakatResult | null {
  return useMemo(() => {
    if (!metalPrices) return null;

    const goldPricePerGram = metalPrices.goldPerGram * currency.rate;
    const silverPricePerGram = metalPrices.silverPerGram * currency.rate;

    let totalAssets = 0;
    let totalLiabilities = 0;

    ASSET_CATEGORIES.forEach((category) => {
      category.fields.forEach((field) => {
        const value = assets[field.id] || 0;
        if (value <= 0) return;

        if (category.id === 'liabilities') {
          totalLiabilities += value;
        } else if (field.type === 'weight_gold') {
          totalAssets += value * goldPricePerGram;
        } else if (field.type === 'weight_silver') {
          totalAssets += value * silverPricePerGram;
        } else {
          totalAssets += value;
        }
      });
    });

    const netWorth = totalAssets - totalLiabilities;
    const goldNisab = GOLD_NISAB_GRAMS * goldPricePerGram;
    const silverNisab = SILVER_NISAB_GRAMS * silverPricePerGram;
    const recommendedNisab = Math.min(goldNisab, silverNisab);
    const meetsNisab = netWorth >= recommendedNisab;
    const zakatDue = meetsNisab ? netWorth * ZAKAT_RATE : 0;

    return {
      totalAssets,
      totalLiabilities,
      netWorth,
      zakatDue,
      meetsNisab,
      goldNisab,
      silverNisab,
    };
  }, [assets, metalPrices, currency]);
}

// ============================================
// Sub-Components
// ============================================

interface NisabInfoCardProps {
  metalPrices: MetalPrices | null;
  loading: boolean;
  currency: Currency;
  onRefresh: () => void;
  isArabic: boolean;
  formatCurrency: (amount: number) => string;
}

const NisabInfoCard = memo(function NisabInfoCard({
  metalPrices,
  loading,
  currency,
  onRefresh,
  isArabic,
  formatCurrency,
}: NisabInfoCardProps) {
  return (
    <section
      aria-label={isArabic ? 'النصاب وأسعار المعادن' : 'Nisab & Metal Prices'}
      className="mb-6 p-4 bg-emerald-50 border border-emerald-200 rounded-xl"
    >
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-emerald-900 flex items-center gap-2">
          <Coins className="w-5 h-5" aria-hidden="true" />
          {isArabic ? 'النصاب وأسعار المعادن' : 'Nisab & Metal Prices'}
        </h2>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="p-1 text-emerald-600 hover:text-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 rounded disabled:opacity-50"
          aria-label={isArabic ? 'تحديث الأسعار' : 'Refresh prices'}
          aria-busy={loading}
        >
          <RefreshCw className={clsx('w-4 h-4', loading && 'animate-spin')} aria-hidden="true" />
        </button>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i}>
              <Skeleton variant="text" width="60%" className="mb-1" />
              <Skeleton variant="text" width="80%" height={24} />
            </div>
          ))}
        </div>
      ) : metalPrices ? (
        <>
          <dl className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <dt className="text-emerald-700">{isArabic ? 'سعر الذهب/جرام' : 'Gold Price/g'}</dt>
              <dd className="font-bold text-emerald-900">
                {formatCurrency(metalPrices.goldPerGram * currency.rate)}
              </dd>
            </div>
            <div>
              <dt className="text-emerald-700">{isArabic ? 'سعر الفضة/جرام' : 'Silver Price/g'}</dt>
              <dd className="font-bold text-emerald-900">
                {formatCurrency(metalPrices.silverPerGram * currency.rate)}
              </dd>
            </div>
            <div>
              <dt className="text-emerald-700">{isArabic ? 'نصاب الذهب' : 'Gold Nisab'}</dt>
              <dd className="font-bold text-emerald-900">
                {formatCurrency(GOLD_NISAB_GRAMS * metalPrices.goldPerGram * currency.rate)}
              </dd>
              <dd className="text-xs text-emerald-600">({GOLD_NISAB_GRAMS}g)</dd>
            </div>
            <div>
              <dt className="text-emerald-700">{isArabic ? 'نصاب الفضة' : 'Silver Nisab'}</dt>
              <dd className="font-bold text-emerald-900">
                {formatCurrency(SILVER_NISAB_GRAMS * metalPrices.silverPerGram * currency.rate)}
              </dd>
              <dd className="text-xs text-emerald-600">({SILVER_NISAB_GRAMS}g)</dd>
            </div>
          </dl>
          <p className="text-xs text-emerald-600 mt-2">
            {isArabic ? 'مصدر الأسعار:' : 'Source:'} {metalPrices.source}
          </p>
        </>
      ) : (
        <p className="text-emerald-700">{isArabic ? 'تعذر تحميل الأسعار' : 'Failed to load prices'}</p>
      )}
    </section>
  );
});

interface AssetFieldInputProps {
  field: AssetField;
  value: number;
  onChange: (value: number) => void;
  currency: Currency;
  isArabic: boolean;
}

const AssetFieldInput = memo(function AssetFieldInput({
  field,
  value,
  onChange,
  currency,
  isArabic,
}: AssetFieldInputProps) {
  const inputId = `asset-${field.id}`;

  return (
    <div>
      <label htmlFor={inputId} className="block text-sm font-medium text-gray-700 mb-1">
        {isArabic ? field.name_ar : field.name_en}
        {field.hint_en && (
          <span className="text-gray-400 font-normal mx-1">
            ({isArabic ? field.hint_ar : field.hint_en})
          </span>
        )}
      </label>
      <div className="relative">
        {field.type === 'currency' && (
          <span
            className={clsx(
              'absolute top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none',
              isArabic ? 'right-3' : 'left-3'
            )}
            aria-hidden="true"
          >
            {currency.symbol}
          </span>
        )}
        <input
          id={inputId}
          type="number"
          min="0"
          step="0.01"
          inputMode="decimal"
          value={value || ''}
          onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
          placeholder="0"
          className={clsx(
            'w-full py-2 border border-gray-300 rounded-lg',
            'focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            field.type === 'currency'
              ? isArabic ? 'pr-10 pl-4' : 'pl-10 pr-4'
              : 'px-4'
          )}
          aria-describedby={field.hint_en ? `${inputId}-hint` : undefined}
        />
        {(field.type === 'weight_gold' || field.type === 'weight_silver') && (
          <span
            className={clsx(
              'absolute top-1/2 -translate-y-1/2 text-gray-500 text-sm pointer-events-none',
              isArabic ? 'left-3' : 'right-3'
            )}
            aria-hidden="true"
          >
            g
          </span>
        )}
      </div>
      {field.hint_en && (
        <p id={`${inputId}-hint`} className="sr-only">
          {isArabic ? field.hint_ar : field.hint_en}
        </p>
      )}
    </div>
  );
});

interface AssetCategoryAccordionProps {
  category: AssetCategory;
  assets: Record<string, number>;
  onAssetChange: (fieldId: string, value: number) => void;
  isExpanded: boolean;
  onToggle: () => void;
  categoryTotal: number;
  currency: Currency;
  isArabic: boolean;
  formatCurrency: (amount: number) => string;
}

const AssetCategoryAccordion = memo(function AssetCategoryAccordion({
  category,
  assets,
  onAssetChange,
  isExpanded,
  onToggle,
  categoryTotal,
  currency,
  isArabic,
  formatCurrency,
}: AssetCategoryAccordionProps) {
  const Icon = category.icon;
  const colors = COLOR_CLASSES[category.color] || COLOR_CLASSES.green;
  const headerId = `category-header-${category.id}`;
  const panelId = `category-panel-${category.id}`;

  return (
    <div
      className={clsx(
        'border-2 rounded-xl overflow-hidden transition-colors',
        isExpanded ? colors.border : 'border-gray-200'
      )}
    >
      <h3>
        <button
          id={headerId}
          onClick={onToggle}
          className="w-full p-4 flex items-center justify-between bg-gray-50 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-emerald-500"
          aria-expanded={isExpanded}
          aria-controls={panelId}
        >
          <div className="flex items-center gap-3">
            <div className={clsx('p-2 rounded-lg', colors.bg)} aria-hidden="true">
              <Icon className={clsx('w-5 h-5', colors.text)} />
            </div>
            <div className={clsx('text-left', isArabic && 'text-right')}>
              <span className="font-semibold text-gray-900 block">
                {isArabic ? category.name_ar : category.name_en}
              </span>
              {categoryTotal > 0 && (
                <span
                  className={clsx(
                    'text-sm',
                    category.id === 'liabilities' ? 'text-red-600' : 'text-gray-500'
                  )}
                >
                  {category.id === 'liabilities' ? '-' : '+'} {formatCurrency(categoryTotal)}
                </span>
              )}
            </div>
          </div>
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-400" aria-hidden="true" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" aria-hidden="true" />
          )}
        </button>
      </h3>

      <div
        id={panelId}
        role="region"
        aria-labelledby={headerId}
        hidden={!isExpanded}
        className={clsx('p-4 space-y-4 bg-white', !isExpanded && 'hidden')}
      >
        {category.fields.map((field) => (
          <AssetFieldInput
            key={field.id}
            field={field}
            value={assets[field.id] || 0}
            onChange={(value) => onAssetChange(field.id, value)}
            currency={currency}
            isArabic={isArabic}
          />
        ))}
      </div>
    </div>
  );
});

interface ZakatSummaryProps {
  result: ZakatResult;
  isArabic: boolean;
  formatCurrency: (amount: number) => string;
}

const ZakatSummary = memo(function ZakatSummary({
  result,
  isArabic,
  formatCurrency,
}: ZakatSummaryProps) {
  return (
    <section
      aria-label={isArabic ? 'ملخص الزكاة' : 'Zakat Summary'}
      className="mb-6 p-6 bg-white border-2 border-emerald-500 rounded-xl"
    >
      <h2 className="font-bold text-lg text-gray-900 mb-4">
        {isArabic ? 'ملخص الزكاة' : 'Zakat Summary'}
      </h2>

      <dl className="space-y-3">
        <div className="flex justify-between">
          <dt className="text-gray-600">{isArabic ? 'إجمالي الأصول' : 'Total Assets'}</dt>
          <dd className="font-semibold text-gray-900 tabular-nums">
            {formatCurrency(result.totalAssets)}
          </dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-gray-600">{isArabic ? 'إجمالي الخصوم' : 'Total Liabilities'}</dt>
          <dd className="font-semibold text-red-600 tabular-nums">
            -{formatCurrency(result.totalLiabilities)}
          </dd>
        </div>
        <hr className="border-gray-200" />
        <div className="flex justify-between">
          <dt className="text-gray-600">{isArabic ? 'صافي الثروة الزكوية' : 'Net Zakatable Wealth'}</dt>
          <dd className="font-bold text-lg text-gray-900 tabular-nums">
            {formatCurrency(result.netWorth)}
          </dd>
        </div>
        <div className="flex justify-between items-center">
          <dt className="text-gray-600">{isArabic ? 'يبلغ النصاب؟' : 'Meets Nisab?'}</dt>
          <dd
            className={clsx(
              'flex items-center gap-1 font-medium',
              result.meetsNisab ? 'text-emerald-600' : 'text-red-600'
            )}
          >
            {result.meetsNisab ? (
              <>
                <CheckCircle className="w-4 h-4" aria-hidden="true" />
                {isArabic ? 'نعم' : 'Yes'}
              </>
            ) : (
              <>
                <AlertCircle className="w-4 h-4" aria-hidden="true" />
                {isArabic ? 'لا' : 'No'}
              </>
            )}
          </dd>
        </div>
        <hr className="border-gray-200" />
        <div className="flex justify-between items-center pt-2">
          <dt className="text-lg font-semibold text-gray-900">
            {isArabic ? 'الزكاة المستحقة (2.5%)' : 'Zakat Due (2.5%)'}
          </dt>
          <dd className="text-2xl font-bold text-emerald-600 tabular-nums" aria-live="polite">
            {formatCurrency(result.zakatDue)}
          </dd>
        </div>
      </dl>

      {!result.meetsNisab && result.netWorth > 0 && (
        <div
          className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800"
          role="status"
        >
          <Info className="w-4 h-4 inline mr-1" aria-hidden="true" />
          {isArabic
            ? 'ثروتك أقل من النصاب. الزكاة ليست واجبة عليك هذا العام.'
            : 'Your wealth is below the Nisab threshold. Zakat is not obligatory for you this year.'}
        </div>
      )}
    </section>
  );
});

interface ZakatRecipientsProps {
  isArabic: boolean;
}

const ZakatRecipients = memo(function ZakatRecipients({ isArabic }: ZakatRecipientsProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <section aria-label={isArabic ? 'مصارف الزكاة' : 'Zakat Recipients'} className="mb-6">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-emerald-600 hover:text-emerald-700 font-medium focus:outline-none focus:underline"
        aria-expanded={isOpen}
      >
        <HelpCircle className="w-5 h-5" aria-hidden="true" />
        {isArabic ? 'مصارف الزكاة الثمانية' : 'Eight Categories of Zakat Recipients'}
      </button>

      {isOpen && (
        <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-xl">
          <p className="text-sm text-gray-600 mb-4 font-arabic text-right" dir="rtl" lang="ar">
            قال الله تعالى: "إِنَّمَا الصَّدَقَاتُ لِلْفُقَرَاءِ وَالْمَسَاكِينِ وَالْعَامِلِينَ عَلَيْهَا وَالْمُؤَلَّفَةِ قُلُوبُهُمْ وَفِي الرِّقَابِ وَالْغَارِمِينَ وَفِي سَبِيلِ اللَّهِ وَابْنِ السَّبِيلِ" (التوبة: 60)
          </p>
          <ul className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {ZAKAT_RECIPIENTS.map((recipient) => (
              <li
                key={recipient.id}
                className="p-2 bg-white rounded-lg border border-gray-100 text-sm"
              >
                <span className="font-medium text-gray-900">
                  {isArabic ? recipient.name_ar : recipient.name_en}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
});

// ============================================
// Main Component
// ============================================

function ZakatCalculatorPageContent() {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';

  // Persistent state
  const [assets, setAssets] = useLocalStorage<Record<string, number>>('zakat_assets', {});
  const [currencyCode, setCurrencyCode] = useLocalStorage('zakat_currency', 'USD');
  const [expandedCategory, setExpandedCategory] = useState<string | null>('cash');

  const selectedCurrency = useMemo(
    () => CURRENCIES.find((c) => c.code === currencyCode) || CURRENCIES[0],
    [currencyCode]
  );

  // Metal prices
  const { prices: metalPrices, loading: loadingPrices, error: pricesError, refetch } = useMetalPrices();

  // Calculate zakat
  const zakatResult = useZakatCalculation(assets, metalPrices ?? null, selectedCurrency);

  // Format currency helper
  const formatCurrency = useCallback(
    (amount: number): string => {
      const formatted = amount.toLocaleString(isArabic ? 'ar-SA' : 'en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
      return `${selectedCurrency.symbol}${formatted}`;
    },
    [selectedCurrency.symbol, isArabic]
  );

  // Calculate category total
  const getCategoryTotal = useCallback(
    (category: AssetCategory): number => {
      if (!metalPrices) return 0;

      const goldPricePerGram = metalPrices.goldPerGram * selectedCurrency.rate;
      const silverPricePerGram = metalPrices.silverPerGram * selectedCurrency.rate;

      return category.fields.reduce((sum, field) => {
        const value = assets[field.id] || 0;
        if (field.type === 'weight_gold') return sum + value * goldPricePerGram;
        if (field.type === 'weight_silver') return sum + value * silverPricePerGram;
        return sum + value;
      }, 0);
    },
    [assets, metalPrices, selectedCurrency.rate]
  );

  // Asset change handler
  const handleAssetChange = useCallback(
    (fieldId: string, value: number) => {
      setAssets((prev) => ({ ...prev, [fieldId]: value }));
    },
    [setAssets]
  );

  return (
    <main
      className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8"
      dir={isArabic ? 'rtl' : 'ltr'}
    >
      {/* Header */}
      <header className="mb-6">
        <Link
          to="/tools"
          className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 mb-4 focus:outline-none focus:underline"
        >
          <ArrowLeft className={clsx('w-4 h-4', isArabic && 'rotate-180')} aria-hidden="true" />
          {isArabic ? 'العودة للأدوات' : 'Back to Tools'}
        </Link>

        <div className="flex items-center gap-3 mb-2">
          <div className="p-3 bg-emerald-100 rounded-lg" aria-hidden="true">
            <Calculator className="w-8 h-8 text-emerald-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {isArabic ? 'حاسبة الزكاة' : 'Zakat Calculator'}
            </h1>
            <p className="text-gray-600">
              {isArabic
                ? 'احسب زكاة مالك بدقة مع أسعار الذهب والفضة الحالية'
                : 'Calculate your Zakat accurately with current gold and silver prices'}
            </p>
          </div>
        </div>
      </header>

      {/* Nisab Info */}
      <NisabInfoCard
        metalPrices={metalPrices ?? null}
        loading={loadingPrices}
        currency={selectedCurrency}
        onRefresh={refetch}
        isArabic={isArabic}
        formatCurrency={formatCurrency}
      />

      {pricesError && (
        <InlineError error={pricesError} onRetry={refetch} className="mb-6" />
      )}

      {/* Currency Selector */}
      <div className="mb-6">
        <label htmlFor="currency-select" className="block text-sm font-medium text-gray-700 mb-2">
          {isArabic ? 'العملة' : 'Currency'}
        </label>
        <select
          id="currency-select"
          value={currencyCode}
          onChange={(e) => setCurrencyCode(e.target.value)}
          className="w-full sm:w-auto px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
        >
          {CURRENCIES.map((currency) => (
            <option key={currency.code} value={currency.code}>
              {currency.symbol} - {isArabic ? currency.name_ar : currency.name_en}
            </option>
          ))}
        </select>
      </div>

      {/* Asset Categories */}
      <div className="mb-6 space-y-4" role="group" aria-label={isArabic ? 'فئات الأصول' : 'Asset Categories'}>
        {ASSET_CATEGORIES.map((category) => (
          <AssetCategoryAccordion
            key={category.id}
            category={category}
            assets={assets}
            onAssetChange={handleAssetChange}
            isExpanded={expandedCategory === category.id}
            onToggle={() => setExpandedCategory(expandedCategory === category.id ? null : category.id)}
            categoryTotal={getCategoryTotal(category)}
            currency={selectedCurrency}
            isArabic={isArabic}
            formatCurrency={formatCurrency}
          />
        ))}
      </div>

      {/* Results */}
      {zakatResult && (
        <ZakatSummary result={zakatResult} isArabic={isArabic} formatCurrency={formatCurrency} />
      )}

      {/* Zakat Recipients */}
      <ZakatRecipients isArabic={isArabic} />

      {/* Disclaimer */}
      <footer className="p-4 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600">
        <p>
          <strong>{isArabic ? 'ملاحظة:' : 'Disclaimer:'}</strong>{' '}
          {isArabic
            ? 'هذه الحاسبة للمساعدة فقط. يرجى استشارة عالم مؤهل للحصول على فتوى دقيقة حسب حالتك.'
            : 'This calculator is for guidance only. Please consult a qualified scholar for a precise ruling based on your situation.'}
        </p>
      </footer>
    </main>
  );
}

// Export with Error Boundary
export function ZakatCalculatorPage() {
  return (
    <ErrorBoundary>
      <ZakatCalculatorPageContent />
    </ErrorBoundary>
  );
}
