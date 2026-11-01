package main

import "fmt"

func main() {
	x := 5
	icount := 0

	if x > 10 {
		fmt.Println("gt10")
	} else if x > 0 {
		for i := 0; i < 12; i++ {
			if i == 1 {
				fmt.Println("deep")
			} else {
				switch i {
					case 2:
						icount := 1
					case 5:
						icount := 3
					case 11:
						icount := 6					
				}
			}
		}
	} else {
		fmt.Println("other")
	}

	n := 0
	for n < 2 {
		n++
	}

	for {
		break
	}

	for range []int{1, 2} {
		fmt.Println("range")
	}

	switch x {
	case 5:
		fmt.Println("five")
	case 3:
		fmt.Println("three")
		if x > icount {
			fmt.Println("Bigger")
		}
	default:
		fmt.Println("other")
	}
}
