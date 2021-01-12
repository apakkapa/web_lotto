select 
 draw_no, 
 draw_date, 
 draw_winners, 
 draw_estimate 
from
 lotto_numbers 
where draw_no>=1910 and draw_no<=1920
order BY
 draw_no DESC