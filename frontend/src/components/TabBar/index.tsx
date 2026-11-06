import Taro from '@tarojs/taro'
import { Text, View } from '@tarojs/components'
import type { TabKey } from '../../types'
import './index.scss'

interface TabBarProps {
  active: TabKey
}

const TABS: { key: TabKey; label: string; page: string }[] = [
  { key: 'home', label: '首页', page: '/pages/index/index' },
  { key: 'map', label: '星图', page: '/pages/quiz/index' },
  { key: 'me', label: '我的', page: '/pages/report/index' }
]

function currentRoute(): string {
  try {
    const pages = Taro.getCurrentPages()
    return pages[pages.length - 1]?.route || ''
  } catch {
    return ''
  }
}

export default function TabBar({ active }: TabBarProps) {
  const handleTap = (page: string, key: TabKey) => {
    if (key === active) return
    Taro.redirectTo({ url: page })
  }

  return (
    <View className='tabbar'>
      {TABS.map((tab) => (
        <View
          key={tab.key}
          className={`tab ${active === tab.key ? 'active' : ''}`}
          onClick={() => handleTap(tab.page, tab.key)}
        >
          <View className={`tab-icon icon-${tab.key}`}>
            {tab.key === 'home' && (
              <View className='planet'>
                <View className='core' />
                <View className='ring' />
              </View>
            )}
            {tab.key === 'map' && (
              <View className='map'>
                <View className='dot d1' />
                <View className='dot d2' />
                <View className='dot d3' />
                <View className='dot d4' />
              </View>
            )}
            {tab.key === 'me' && (
              <View className='me'>
                <View className='head' />
                <View className='body' />
              </View>
            )}
          </View>
          <Text className='tab-label'>{tab.label}</Text>
        </View>
      ))}
    </View>
  )
}
