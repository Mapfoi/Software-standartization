package main

import "fmt"

func main() {
	x := 5

	if x > 10 {
		fmt.Println("gt10")
	} else if x > 0 {
		for i := 0; i < 3; i++ {
			if i == 1 {
				fmt.Println("deep")
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
	default:
		fmt.Println("other")
	}
}