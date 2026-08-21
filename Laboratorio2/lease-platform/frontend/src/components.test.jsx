import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Empty, Money, Notice, StatusBadge } from './components'

describe('shared accessible states', () => {
  it('exposes errors through an alert role', () => {
    render(<Notice error="RUC inválido" />)
    expect(screen.getByRole('alert')).toHaveTextContent('RUC inválido')
  })

  it('renders explicit empty and status states', () => {
    render(<><Empty>Sin solicitudes</Empty><StatusBadge value="IN_REVIEW" /></>)
    expect(screen.getByText('Sin solicitudes')).toBeVisible()
    expect(screen.getByText('IN REVIEW')).toBeVisible()
  })

  it('formats contract currency without losing the amount', () => {
    render(<Money amount="250000.00" currency="PEN" />)
    expect(screen.getByText(/250.000/)).toBeVisible()
  })
})
