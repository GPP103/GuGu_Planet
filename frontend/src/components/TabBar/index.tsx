import Taro from '@tarojs/taro'
import { Text, View } from '@tarojs/components'
import type { TabKey } from '../../types'
import './index.scss'

interface TabBarProps {
  active: TabKey
}

const TABS: { key: TabKey; label: string; page: string }[] = [
  { key: 'home', label: '首页', page: '/pages/index/index' },
  { key: 'records', label: '记录', page: '/pages/records/index' },
  { key: 'me', label: '我的', page: '/pages/profile/index' }
]

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
            {tab.key === 'records' && (
              <View className='records'>
                <View className='line l1' />
                <View className='line l2' />
                <View className='line l3' />
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
