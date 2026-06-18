import React from 'react'

const HEADERS = new Set(['SUMMARY', 'EXPERIENCE', 'PROJECTS', 'TECHNICAL SKILLS', 'SKILLS', 'EDUCATION'])

interface Props {
  text: string
}

export default function ResumePreview({ text }: Props) {
  const lines = text.split('\n')
  let section = ''
  const elements: React.ReactNode[] = []
  let i = 0
  let isFirstLine = true

  for (const raw of lines) {
    const line = raw.trim()
    if (!line) {
      i++
      continue
    }

    const upper = line.toUpperCase().replace(/:$/, '')
    if (upper === 'HEADER') {
      section = 'HEADER'
      i++
      continue
    }

    if (HEADERS.has(upper)) {
      section = upper
      elements.push(
        <div key={i} className="mt-4 mb-1">
          <div className="text-[10px] font-bold tracking-[0.15em] uppercase text-gray-700 border-b border-gray-300 pb-0.5">
            {line}
          </div>
        </div>,
      )
    } else if (section === 'HEADER') {
      if (isFirstLine) {
        elements.push(
          <div key={i} className="text-xl font-bold text-center text-gray-900 mb-0.5">
            {line}
          </div>,
        )
        isFirstLine = false
      } else {
        elements.push(
          <div key={i} className="text-[10px] text-center text-gray-500 mb-2">
            {line}
          </div>,
        )
      }
    } else if (section === 'EXPERIENCE' && line.includes(' at ') && line.split(' ').length <= 12) {
      elements.push(
        <div key={i} className="text-[11px] font-semibold text-gray-800 mt-1.5">
          {line}
        </div>,
      )
    } else {
      elements.push(
        <div key={i} className="text-[10.5px] text-gray-600 leading-[1.6] my-[1px]">
          {line}
        </div>,
      )
    }
    i++
  }

  return (
    <div className="bg-white rounded-xl shadow-2xl overflow-y-auto max-h-[70vh]">
      <div className="px-10 py-8 font-sans" style={{ fontFamily: 'Arial, sans-serif' }}>
        {elements}
      </div>
    </div>
  )
}
