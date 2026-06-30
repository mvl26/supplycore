// @vitest-environment happy-dom
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'

// FormField nhập Link gọi api/schemas — mock để cô lập, ta chỉ test Currency.
vi.mock('../src/api.js', () => ({ call: vi.fn(async () => []) }))
vi.mock('../src/schemas.js', () => ({ QUICK_CREATE: {} }))

import FormField from '../src/components/FormField.vue'

const currencyField = { name: 'unit_price', label: 'Đơn giá', type: 'Currency' }

function mountCurrency(value) {
  return mount(FormField, {
    props: { field: currencyField, modelValue: value, showLabel: false },
  })
}

describe('FormField Currency — phân tách hàng nghìn', () => {
  it('hiển thị giá trị số với dấu . ngăn hàng nghìn (vi-VN)', () => {
    const w = mountCurrency(1234567)
    expect(w.get('input').element.value).toBe('1.234.567')
  })

  it('rỗng/null → input rỗng', () => {
    const w = mountCurrency(null)
    expect(w.get('input').element.value).toBe('')
  })

  it('nhập chữ số → emit số nguyên + hiển thị có dấu .', async () => {
    const w = mountCurrency(null)
    const input = w.get('input')
    input.element.value = '15000'
    await input.trigger('input')
    expect(w.emitted('update:modelValue').at(-1)).toEqual([15000])
    expect(input.element.value).toBe('15.000')
  })

  it('gõ "00" khi đang 0 vẫn buộc về "0" (không kẹt 00)', async () => {
    const w = mountCurrency(0)
    const input = w.get('input')
    // mô phỏng người dùng gõ thêm '0' → DOM thành '00'
    input.element.value = '00'
    await input.trigger('input')
    expect(input.element.value).toBe('0')
    expect(w.emitted('update:modelValue').at(-1)).toEqual([0])
  })

  it('ký tự lạ bị loại, giá trị không kẹt trong ô', async () => {
    const w = mountCurrency(1234)
    const input = w.get('input')
    input.element.value = '1.234a'
    await input.trigger('input')
    expect(input.element.value).toBe('1.234')
    expect(w.emitted('update:modelValue').at(-1)).toEqual([1234])
  })

  it('xoá hết → emit null, ô rỗng', async () => {
    const w = mountCurrency(500)
    const input = w.get('input')
    input.element.value = ''
    await input.trigger('input')
    expect(input.element.value).toBe('')
    expect(w.emitted('update:modelValue').at(-1)).toEqual([null])
  })

  it('readonly → không emit khi input', async () => {
    const w = mount(FormField, {
      props: { field: currencyField, modelValue: 100, showLabel: false, readonly: true },
    })
    const input = w.get('input')
    input.element.value = '999'
    await input.trigger('input')
    expect(w.emitted('update:modelValue')).toBeUndefined()
  })
})
