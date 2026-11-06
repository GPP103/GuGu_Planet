import { Text, View } from '@tarojs/components'
import './index.scss'

interface MascotProps {
  variant?: 'hero' | 'loading' | 'empty' | 'celebrate'
  className?: string
}

export default function Mascot({ variant = 'hero', className = '' }: MascotProps) {
  return (
    <View className={`mascot mascot-${variant} ${className}`}>
      {variant === 'hero' && <View className='halo' />}
      {variant === 'empty' && <Text className='deco'>?</Text>}
      {variant === 'celebrate' && <View className='deco star'>★</View>}
      <View className='wing wing-l' />
      <View className='wing wing-r' />
      <View className='body'>
        <View className='belly' />
        <View className='eye eye-l' />
        <View className='eye eye-r' />
        <View className='beak' />
        <View className='blush blush-l' />
        <View className='blush blush-r' />
      </View>
      <View className='ahoge' />
    </View>
  )
}
