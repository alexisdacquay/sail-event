import '@testing-library/jest-dom'
import { configure } from '@testing-library/react'

// CI runners are several times slower than a laptop; 1 s default waits flake there.
configure({ asyncUtilTimeout: 5000 })
